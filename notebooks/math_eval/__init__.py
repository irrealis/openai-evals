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
  def as_dict(self, keys=None):
    if keys is None:
      keys = self.__table__.columns.keys()
    return {key:getattr(self, key) for key in keys}

  def repr(self, name=None, keys=None):
    if name is None:
      name = self.__class__.__name__
    return f'<{name}: {self.as_dict()}>'

  def __repr__(self):
    return self.repr()

  @classmethod
  def get(cls, session, **search_dict):
    statement = sa.select(cls).filter_by(**search_dict)
    return session.scalars(statement).one_or_none()

  @classmethod
  def get_or_create(cls, session, search_dict, create_dict = None, update = False, use_null = False):
    create_dict = create_dict or {}
    item = cls.get(session, **search_dict)
    if item is None:
      search_dict.update(create_dict)
      item = cls(**search_dict)
      session.add(item)
    elif update:
      for k,v in create_dict.items():
        if use_null or (v is not None):
          setattr(item, k, v)
    return item

  @classmethod
  def update_or_create(cls, session, search_dict, update_dict, use_null = False):
    return cls.get_or_create(session, search_dict, update_dict, update=True, use_null=use_null)


problem_set_problem_associations_table = Table(
  'problem_set_problem_associations',
  Base.metadata,
  Column('problem_set_id', ForeignKey('problem_sets.id'), primary_key=True),
  Column('problem_id', ForeignKey('problems.id'), primary_key=True),
)
submission_set_submission_associations_table = Table(
  'submission_set_submission_associations',
  Base.metadata,
  Column('submission_set_id', ForeignKey('submission_sets.id'), primary_key=True),
  Column('submission_id', ForeignKey('submissions.id'), primary_key=True),
)
evaluation_set_evaluation_associations_table = Table(
  'evaluation_set_evaluation_associations',
  Base.metadata,
  Column('evaluation_set_id', ForeignKey('evaluation_sets.id'), primary_key=True),
  Column('evaluation_id', ForeignKey('evaluations.id'), primary_key=True),
)


class Model(Base):
  __tablename__ = 'models'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  #notes: Mapped[str] = mapped_column(String, default='')

  submissions: Mapped[List['Submission']] = relationship(back_populates="model")
  evaluations: Mapped[List['Evaluation']] = relationship(back_populates="model")

class Problem(Base):
  __tablename__ = 'problems'
  id: Mapped[int] = mapped_column(primary_key=True)
  input: Mapped[str] = mapped_column(String, default='')
  ideal: Mapped[str] = mapped_column(String, default='')
  rubric: Mapped[str] = mapped_column(String, default='')
  #notes: Mapped[str] = mapped_column(String, default='')

  submissions: Mapped[List['Submission']] = relationship(back_populates="problem")
  problem_sets: Mapped[List['ProblemSet']] = relationship(
    secondary=problem_set_problem_associations_table,
    back_populates='problems'
  )

class Submission(Base):
  __tablename__ = 'submissions'
  id: Mapped[int] = mapped_column(primary_key=True)
  completion: Mapped[str] = mapped_column(String, default='')
  score: Mapped[Decimal] = mapped_column(Numeric, default=Decimal('0'))
  is_example: Mapped[bool] = mapped_column(Boolean, default=False)
  #notes: Mapped[str] = mapped_column(String, default='')
  model_id: Mapped[int] = mapped_column(ForeignKey('models.id'), nullable=True)
  problem_id: Mapped[int] = mapped_column(ForeignKey('problems.id'), nullable=True)

  model: Mapped[List['Model']] = relationship(back_populates="submissions")
  problem: Mapped['Problem'] = relationship(back_populates="submissions")
  evaluations: Mapped[List['Evaluation']] = relationship(back_populates="submission")
  submission_sets: Mapped[List['SubmissionSet']] = relationship(
    secondary=submission_set_submission_associations_table,
    back_populates="submissions"
  )

class Evaluation(Base):
  __tablename__ = 'evaluations'
  id: Mapped[int] = mapped_column(primary_key=True)
  completion: Mapped[str] = mapped_column(String, default='')
  score: Mapped[Decimal] = mapped_column(Numeric, default=Decimal('0'))
  is_example: Mapped[bool] = mapped_column(Boolean, default=False)
  #notes: Mapped[str] = mapped_column(String, default='')
  model_id: Mapped[int] = mapped_column(ForeignKey('models.id'), nullable=True)
  submission_id: Mapped[int] = mapped_column(ForeignKey('submissions.id'), nullable=True)

  model: Mapped[List['Model']] = relationship(back_populates="evaluations")
  submission: Mapped['Submission'] = relationship(back_populates="evaluations")
  evaluation_sets: Mapped[List['EvaluationSet']] = relationship(
    secondary=evaluation_set_evaluation_associations_table,
    back_populates="evaluations"
  )

class ProblemSet(Base):
  __tablename__ = 'problem_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  #notes: Mapped[str] = mapped_column(String, default='')

  problems: Mapped[List['Problem']] = relationship(
    secondary=problem_set_problem_associations_table,
    back_populates="problem_sets"
  )


class SubmissionSet(Base):
  __tablename__ = 'submission_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  #notes: Mapped[str] = mapped_column(String, default='')

  submissions: Mapped[List['Submission']] = relationship(
    secondary=submission_set_submission_associations_table,
    back_populates="submission_sets"
  )


class EvaluationSet(Base):
  __tablename__ = 'evaluation_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  #notes: Mapped[str] = mapped_column(String, default='')

  evaluations: Mapped[List['Evaluation']] = relationship(
    secondary=evaluation_set_evaluation_associations_table,
    back_populates="evaluation_sets"
  )


