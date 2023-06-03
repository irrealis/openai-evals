import sqlalchemy as sa

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Table

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

import json
from ruamel.yaml.scalarstring import LiteralScalarString

from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from typing import List
from typing import Optional


class Base(DeclarativeBase):
  def repr(self, *ks):
    attrs = ', '.join(f'{k}={getattr(self, k)}' for k in ks)
    return f'<{self.__class__.__name__}({attrs})>'

  @classmethod
  def get_or_create(cls, session, search_dict, create_dict = None, update = False):
    create_dict = create_dict or {}
    statement = sa.select(cls).filter_by(**search_dict)
    item = session.scalars(statement).one_or_none()
    if item is None:
      search_dict.update(create_dict)
      session.add(cls(**search_dict))
      item = session.scalars(statement).one_or_none()
    elif update:
      for k,v in create_dict.items():
        setattr(item, k, v)
    return item

  @classmethod
  def update_or_create(cls, session, search_dict, update_dict):
    return cls.get_or_create(session, search_dict, update_dict, update=True)


class Model(Base):
  __tablename__ = 'models'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  notes_json: Mapped[str] = mapped_column(String, default='""')
  is_example: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  submissions: Mapped[List['Submission']] = relationship(back_populates="model")
  evaluations: Mapped[List['Evaluation']] = relationship(back_populates="model")

  def __repr__(self):
    return self.repr('id', 'name', 'notes', 'is_example')

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)


problem_set_problem_associations_table = Table(
  'problem_set_problem_associations',
  Base.metadata,
  Column('problem_set_id', ForeignKey('problem_sets.id'), primary_key=True),
  Column('problem_id', ForeignKey('problems.id'), primary_key=True),
)

class ProblemSet(Base):
  __tablename__ = 'problem_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  notes_json: Mapped[str] = mapped_column(String, default='""')
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  problems: Mapped[List['Problem']] = relationship(
    secondary=problem_set_problem_associations_table,
    back_populates="problem_sets"
  )

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def __repr__(self):
    return self.repr('id', 'name', 'notes')

class Problem(Base):
  __tablename__ = 'problems'
  id: Mapped[int] = mapped_column(primary_key=True)
  input: Mapped[str] = mapped_column(String, default='')
  ideal: Mapped[str] = mapped_column(String, default='')
  rubric: Mapped[str] = mapped_column(String, default='')
  notes_json: Mapped[str] = mapped_column(String, default='""')
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  submissions: Mapped[List['Submission']] = relationship(back_populates="problem")
  problem_sets: Mapped[List['ProblemSet']] = relationship(
    secondary=problem_set_problem_associations_table,
    back_populates="problems"
  )

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def __repr__(self):
    return self.repr('id', 'notes')


submission_set_submission_associations_table = Table(
  'submission_set_submission_associations',
  Base.metadata,
  Column('submission_set_id', ForeignKey('submission_sets.id'), primary_key=True),
  Column('submission_id', ForeignKey('submissions.id'), primary_key=True),
)

class SubmissionSet(Base):
  __tablename__ = 'submission_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  notes_json: Mapped[str] = mapped_column(String, default='""')
  is_example: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  submissions: Mapped[List['Submission']] = relationship(
    secondary=submission_set_submission_associations_table,
    back_populates="submission_sets"
  )

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def __repr__(self):
    return self.repr('id', 'name', 'notes', 'is_example')


class Submission(Base):
  __tablename__ = 'submissions'
  id: Mapped[int] = mapped_column(primary_key=True)
  completion_json: Mapped[str] = mapped_column(String, default='""')
  message: Mapped[str] = mapped_column(String, default='')
  score: Mapped[Decimal] = mapped_column(Numeric, default=Decimal('0'))
  notes_json: Mapped[str] = mapped_column(String, default='""')
  is_example: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  model_id: Mapped[int] = mapped_column(ForeignKey('models.id'))
  model: Mapped[List['Model']] = relationship(back_populates="submissions")
  problem_id: Mapped[int] = mapped_column(ForeignKey('problems.id'))
  problem: Mapped['Problem'] = relationship(back_populates="submissions")
  evaluations: Mapped[List['Evaluation']] = relationship(back_populates="submission")
  submission_sets: Mapped[List['SubmissionSet']] = relationship(
    secondary=submission_set_submission_associations_table,
    back_populates="submissions"
  )

  @property
  def completion(self):
    return json.loads(self.completion_json)
  @completion.setter
  def completion(self, data):
    self.completion_json = json.dumps(data)

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def __repr__(self):
    return self.repr('id', 'score', 'notes', 'model_id', 'problem_id')



evaluation_set_evaluation_associations_table = Table(
  'evaluation_set_evaluation_associations',
  Base.metadata,
  Column('evaluation_set_id', ForeignKey('evaluation_sets.id'), primary_key=True),
  Column('evaluation_id', ForeignKey('evaluations.id'), primary_key=True),
)

class EvaluationSet(Base):
  __tablename__ = 'evaluation_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  notes_json: Mapped[str] = mapped_column(String, default='""')
  is_example: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  evaluations: Mapped[List['Evaluation']] = relationship(
    secondary=evaluation_set_evaluation_associations_table,
    back_populates="evaluation_sets"
  )

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def __repr__(self):
    return self.repr('id', 'name', 'notes', 'is_example')

class Evaluation(Base):
  __tablename__ = 'evaluations'
  id: Mapped[int] = mapped_column(primary_key=True)
  completion_json: Mapped[str] = mapped_column(String, default='""')
  message: Mapped[str] = mapped_column(String, default='')
  score: Mapped[Decimal] = mapped_column(Numeric, default=Decimal('0'))
  notes_json: Mapped[str] = mapped_column(String, default='""')
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  model_id: Mapped[int] = mapped_column(ForeignKey('models.id'))
  model: Mapped[List['Model']] = relationship(back_populates="evaluations")
  submission_id: Mapped[int] = mapped_column(ForeignKey('submissions.id'))
  submission: Mapped['Submission'] = relationship(back_populates="evaluations")
  evaluation_sets: Mapped[List['EvaluationSet']] = relationship(
    secondary=evaluation_set_evaluation_associations_table,
    back_populates="evaluations"
  )

  @property
  def completion(self):
    return json.loads(self.completion_json)
  @completion.setter
  def completion(self, data):
    self.completion_json = json.dumps(data)

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def __repr__(self):
    return self.repr('id', 'score', 'notes', 'model_id', 'submission_id')