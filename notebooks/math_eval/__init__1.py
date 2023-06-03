import sqlalchemy as sa

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Boolean

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
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  submission_sets: Mapped[List['SubmissionSet']] = relationship(back_populates="model")
  evaluation_sets: Mapped[List['EvaluationSet']] = relationship(back_populates="model")

  def __repr__(self):
    return self.repr('id', 'name')

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def to_ydict(self):
    return dict(
      name=self.name,
      notes=self.notes,
      model_id=self.id,
      created_at=self.created_at,
      updated_at=self.updated_at,
    )

class ProblemSet(Base):
  __tablename__ = 'problem_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  notes_json: Mapped[str] = mapped_column(String, default='""')
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  problems: Mapped[List['Problem']] = relationship(back_populates="problem_set")

  def __repr__(self):
    return self.repr('id', 'name', 'notes_json')

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def to_ydict(self):
    return dict(
      name=self.name,
      notes=self.notes,
      problem_set_size=len(self.problems),
      problem_set_id=self.id,
      created_at=self.created_at,
      updated_at=self.updated_at,
    )

  def export_ydict(self):
    problems_dict = [problem.to_ydict() for problem in self.problems]
    meta = dict(
      data_exported_at=datetime.utcnow(),
      problems_listed=len(problems_dict),
    )
    return dict(
      meta=meta,
      problem_sets=[self.to_ydict()],
      problems=problems_dict,
    )


class Problem(Base):
  __tablename__ = 'problems'
  id: Mapped[int] = mapped_column(primary_key=True)
  input: Mapped[str] = mapped_column(String, default='')
  ideal: Mapped[str] = mapped_column(String, default='')
  rubric: Mapped[str] = mapped_column(String, default='')
  notes_json: Mapped[str] = mapped_column(String, default='""')
  problem_set_id: Mapped[int] = mapped_column(ForeignKey('problem_sets.id'))
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  problem_set: Mapped['ProblemSet'] = relationship(back_populates="problems")
  submissions: Mapped[List['Submission']] = relationship(back_populates="problem")

  def __repr__(self):
    return self.repr('id', 'problem_set_id')

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def to_ydict(self):
    return dict(
      input=LiteralScalarString(self.input),
      ideal=LiteralScalarString(self.ideal),
      rubric=LiteralScalarString(self.rubric),
      notes=self.notes,
      problem_id=self.id,
      problem_set_id=self.problem_set_id,
      created_at=self.created_at,
      updated_at=self.updated_at,
    )

class SubmissionSet(Base):
  __tablename__ = 'submission_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  notes_json: Mapped[str] = mapped_column(String, default='""')
  model_id: Mapped[int] = mapped_column(ForeignKey('models.id'))
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  model: Mapped[List['Model']] = relationship(back_populates="submission_sets")
  submissions: Mapped[List['Submission']] = relationship(back_populates="submission_set")

  def __repr__(self):
    return self.repr('id', 'name', 'notes_json', 'model_id')

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def to_ydict(self):
    return dict(
      name=self.name,
      notes=self.notes,
      submission_set_size=len(self.submissions),
      submission_set_id=self.id,
      model_id=self.model_id,
      created_at=self.created_at,
      updated_at=self.updated_at,
    )

  def export_ydict(self):
    problem_sets_dict = {}
    problems_dict = {}
  
    for submission in self.submissions:
      problem = submission.problem
  
      # Save the problem set if not already saved.
      if problem.problem_set.id not in problem_sets_dict:
        problem_sets_dict[problem.problem_set.id] = problem.problem_set.to_ydict()
  
      # Load or create the problem dict.
      if problem.id in problems_dict:
        problem_dict = problems_dict[problem.id]
      else:
        problem_dict = problem.to_ydict()
  
      # Save the submission dict.
      problem_submissions = problem_dict.get('submissions', {})
      problem_submissions[submission.id] = submission.to_ydict()
      problem_dict['submissions'] = problem_submissions
  
      # Save the problem dict.
      problems_dict[problem.id] = problem_dict
  
    # Convert each problem's submissions dict to a list.
    for k in problems_dict.keys():
      problems_dict[k]['submissions'] = list(problems_dict[k]['submissions'].values())
  
    meta = dict(
      data_exported_at=datetime.utcnow(),
      problems_listed=len(problems_dict),
      submissions_listed=len(self.submissions),
    )
    return dict(
      meta=meta,
      models=[self.model.to_ydict()],
      problem_sets=list(problem_sets_dict.values()),
      submission_sets=[self.to_ydict()],
      problems=list(problems_dict.values()),
    )

class Submission(Base):
  __tablename__ = 'submissions'
  id: Mapped[int] = mapped_column(primary_key=True)
  completion_json: Mapped[str] = mapped_column(String, default='""')
  message: Mapped[str] = mapped_column(String, default='')
  score: Mapped[Decimal] = mapped_column(Numeric, default=Decimal('0'))
  notes_json: Mapped[str] = mapped_column(String, default='""')
  is_example: Mapped[bool] = mapped_column(Boolean, default=False)
  problem_id: Mapped[int] = mapped_column(ForeignKey('problems.id'))
  submission_set_id: Mapped[int] = mapped_column(ForeignKey('submission_sets.id'))
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  problem: Mapped['Problem'] = relationship(back_populates="submissions")
  submission_set: Mapped['SubmissionSet'] = relationship(back_populates="submissions")
  evaluations: Mapped[List['Evaluation']] = relationship(back_populates="submission")

  def __repr__(self):
    return self.repr('id', 'score', 'notes_json', 'problem_id', 'submission_set_id')

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

  def to_ydict(self):
    return dict(
      completion=self.completion,
      message=LiteralScalarString(self.message),
      score=self.score,
      notes=self.notes,
      is_example=self.is_example,
      submission_id=self.id,
      submission_set_id=self.submission_set_id,
      created_at=self.created_at,
      updated_at=self.updated_at,
    )

class EvaluationSet(Base):
  __tablename__ = 'evaluation_sets'
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String)
  notes_json: Mapped[str] = mapped_column(String, default='""')
  model_id: Mapped[int] = mapped_column(ForeignKey('models.id'))
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  model: Mapped[List['Model']] = relationship(back_populates="evaluation_sets")
  evaluations: Mapped[List['Evaluation']] = relationship(back_populates="evaluation_set")

  def __repr__(self):
    return self.repr('id', 'name', 'notes_json', 'model_id')

  @property
  def notes(self):
    return json.loads(self.notes_json)
  @notes.setter
  def notes(self, data):
    self.notes_json = json.dumps(data)

  def to_ydict(self):
    return dict(
      name=self.name,
      notes=self.notes,
      evaluation_set_size=len(self.evaluations),
      evaluation_set_id=self.id,
      model_id=self.model_id,
      created_at=self.created_at,
      updated_at=self.updated_at,
    )

  def export_ydict(self):
    models_dict = {}
    submission_sets_dict = {}
    problem_sets_dict = {}
    problems_dict = {}
    submissions_dict = {}
  
    for evaluation in self.evaluations:
      submission = evaluation.submission
      problem = submission.problem
  
      ss = submission.submission_set
      ps = problem.problem_set
  
      ## Save submission set, problem set, and models.
  
      # Save the submission set if not already saved.
      if ss.id not in submission_sets_dict:
        submission_sets_dict[ss.id] = ss.to_ydict()
  
      # Save the problem set if not already saved.
      if ps.id not in problem_sets_dict:
        problem_sets_dict[ps.id] = ps.to_ydict()
  
      # Save the models if not already saved.
      if ss.model.id not in models_dict:
        models_dict[ss.model.id] = ss.model.to_ydict()
      if self.model.id not in models_dict:
        models_dict[self.model.id] = self.model.to_ydict()
  
      ## Load the problem dict, submission dict, and evaluation dict.
  
      # Load or create the problem dict.
      if problem.id in problems_dict:
        problem_dict = problems_dict[problem.id]
      else:
        problem_dict = problem.to_ydict()
  
      # Load or create the submission dict.
      problem_submissions = problem_dict.get('submissions', {})
      if submission.id in problem_submissions:
        submission_dict = problem_submissions[submission.id]
      else:
        submission_dict = submission.to_ydict()
  
      # Load or create the evaluation dict.
      submission_evaluations = submission_dict.get('evaluations', {})
      if evaluation.id in submission_evaluations:
        evaluation_dict = submission_evaluations[evaluation.id]
      else:
        evaluation_dict = evaluation.to_ydict()
      
      ## Load the evaluation dict, submission dict, and problem dict.
      ## Note that this is done in reverse order, from the bottom of the hierarchy
      ## upward, to ensure that the top of the hierarchy has all changes.
  
      # Save the evaluation dict.
      submission_evaluations[evaluation.id] = evaluation_dict
      submission_dict['evaluations'] = submission_evaluations
  
      # Save the submission dict.
      problem_submissions[submission.id] = submission_dict
      submissions_dict[submission.id] = submission_dict
      problem_dict['submissions'] = problem_submissions
  
      # Save the problem dict.
      problems_dict[problem.id] = problem_dict
  
    # Convert each problem's submissions dict to a list.
    for pk in problems_dict.keys():
      for sk in problems_dict[pk]['submissions'].keys():
        problems_dict[pk]['submissions'][sk]['evaluations'] = list(
          problems_dict[pk]['submissions'][sk]['evaluations'].values()
        )
      problems_dict[pk]['submissions'] = list(
        problems_dict[pk]['submissions'].values()
      )

    meta = dict(
      data_exported_at=datetime.utcnow(),
      problems_listed=len(problems_dict),
      submissions_listed=len(submissions_dict),
      evaluations_listed=len(self.evaluations),
    )
    return dict(
      meta = meta,
      models=list(models_dict.values()),
      problem_sets=list(problem_sets_dict.values()),
      submission_sets=list(submission_sets_dict.values()),
      evaluation_sets=[self.to_ydict()],
      problems=list(problems_dict.values()),
    )

class Evaluation(Base):
  __tablename__ = 'evaluations'
  id: Mapped[int] = mapped_column(primary_key=True)
  completion_json: Mapped[str] = mapped_column(String, default='""')
  message: Mapped[str] = mapped_column(String, default='')
  score: Mapped[Decimal] = mapped_column(Numeric, default=Decimal('0'))
  notes_json: Mapped[str] = mapped_column(String, default='""')
  submission_id: Mapped[int] = mapped_column(ForeignKey('submissions.id'))
  evaluation_set_id: Mapped[int] = mapped_column(ForeignKey('evaluation_sets.id'))
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  submission: Mapped['Submission'] = relationship(back_populates="evaluations")
  evaluation_set: Mapped['EvaluationSet'] = relationship(back_populates="evaluations")

  def __repr__(self):
    return self.repr('id', 'score', 'notes_json', 'submission_id', 'evaluation_set_id')

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

  def to_ydict(self):
    return dict(
      completion=self.completion,
      message=LiteralScalarString(self.message),
      score=self.score,
      notes=self.notes,
      evaluation_id=self.id,
      evaluation_set_id=self.evaluation_set_id,
      created_at=self.created_at,
      updated_at=self.updated_at,
    )
