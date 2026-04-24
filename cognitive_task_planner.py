"""
Cognitive Load-Aware Task Planning System
Implementation based on HCI-ML principles with controlled growth mechanism
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MentalEffort(Enum):
    """User-defined mental effort levels"""
    LOW = 1      # Routine, automatic
    MEDIUM = 2   # Focused but manageable
    HIGH = 3     # Deep thinking, exhausting


class UserState(Enum):
    """System behavior states based on data availability"""
    NEW_USER = "new"              # 0-9 days: baseline rules only
    LEARNING_USER = "learning"    # 10-20 days: capacity calibration
    ESTABLISHED_USER = "established"  # 20+ days: personalized + exploration


@dataclass
class Task:
    """Individual task representation"""
    name: str
    mental_effort: MentalEffort
    duration_minutes: int
    deadline: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Task name cannot be empty")
        if self.duration_minutes is None:
            defaults = {
                MentalEffort.LOW: 30,
                MentalEffort.MEDIUM: 60,
                MentalEffort.HIGH: 90
            }
            self.duration_minutes = defaults[self.mental_effort]
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")


@dataclass
class DailyOutcome:
    """Record of a day's planning and execution"""
    date: datetime
    planned_load: float
    actual_completion_rate: float
    task_count: int
    high_effort_count: int
    had_deadline: bool
    day_of_week: int
    success: bool  # True if completion_rate >= 0.7
    capacity_limit_at_time: Optional[float] = None  # EMA limit captured before update


class CognitiveLoadCalculator:
    """
    Rule-based cognitive cost computation
    NO ML HERE - preserves user intent and interpretability
    """
    
    def __init__(self, alpha: float = 0.10):
        """
        Args:
            alpha: Duration sensitivity base per effort unit.
                   Effective alpha = alpha × effort_value, giving
                   LOW=0.10, MEDIUM=0.20, HIGH=0.30 — higher effort
                   tasks accumulate fatigue faster with duration.
        """
        self.alpha = alpha

    def compute_task_cost(self, task: Task) -> float:
        """
        Computes cognitive cost for a single task.

        Formula: Effort × (1 + α_eff × Duration/60)
        where α_eff = alpha × effort_value

        HIGH effort tasks receive a steeper duration penalty than LOW,
        reflecting that cognitively demanding work fatigues faster.
        """
        alpha_effective = self.alpha * task.mental_effort.value
        duration_modifier = 1 + alpha_effective * (task.duration_minutes / 60)
        cognitive_cost = task.mental_effort.value * duration_modifier
        return cognitive_cost
    
    def compute_daily_load(self, tasks: List[Task]) -> float:
        """Sum of all task cognitive costs for the day"""
        return sum(self.compute_task_cost(task) for task in tasks)
    
    def get_task_breakdown(self, tasks: List[Task]) -> Dict:
        """Detailed breakdown for user transparency"""
        breakdown = {
            'total_load': self.compute_daily_load(tasks),
            'task_costs': [(t.name, self.compute_task_cost(t)) for t in tasks],
            'total_time_minutes': sum(t.duration_minutes for t in tasks),
            'effort_distribution': {
                'low': sum(1 for t in tasks if t.mental_effort == MentalEffort.LOW),
                'medium': sum(1 for t in tasks if t.mental_effort == MentalEffort.MEDIUM),
                'high': sum(1 for t in tasks if t.mental_effort == MentalEffort.HIGH)
            }
        }
        return breakdown


class CapacityLearner:
    """
    Learns user's daily cognitive capacity via Exponential Moving Average.
    Updates from day 1, handles failures via completion-rate weighting,
    and guards against anomalies.
    """

    def __init__(self):
        self.history: List[DailyOutcome] = []
        self.current_limit: Optional[float] = None
        self.limit_set_date: Optional[datetime] = None

    def add_outcome(self, outcome: DailyOutcome):
        self.history.append(outcome)

    def get_user_state(self) -> UserState:
        days = len(self.history)
        if days < 5:
            return UserState.NEW_USER
        elif days < 15:
            return UserState.LEARNING_USER
        else:
            return UserState.ESTABLISHED_USER

    def update_limit(self, outcome: DailyOutcome, alpha: float = 0.3):
        """
        EMA-based capacity update.

        observed_sustainable = planned_load × completion_rate
          → full success pushes limit toward planned load
          → failure pulls it down proportionally

        Anomaly guard: skip update if load is wildly outside current belief.
        Adaptive α: trust observations less when they are far from current limit.
        Single-day cap: limit cannot move more than ±0.75 per update.
        """
        planned = outcome.planned_load

        # Anomaly guard — ignore extreme outliers
        if self.current_limit is not None:
            if planned > self.current_limit * 2.0 or planned < self.current_limit * 0.3:
                return

            # Only learn from surprising outcomes — expected results are uninformative
            over_limit = planned > self.current_limit
            success = outcome.actual_completion_rate >= 0.7
            if over_limit != success:
                return

        observed = planned * outcome.actual_completion_rate

        if self.current_limit is None:
            # Seed from first real outcome
            self.current_limit = round(max(observed, 1.0), 3)
            self.limit_set_date = datetime.now()
            return

        # Adaptive α: reduce trust when observation is far from current belief
        distance_ratio = abs(observed - self.current_limit) / max(self.current_limit, 0.1)
        effective_alpha = alpha * max(0.3, 1.0 - distance_ratio)

        new_limit = effective_alpha * observed + (1 - effective_alpha) * self.current_limit

        # Cap single-day movement at ±0.75
        delta = max(-0.75, min(0.75, new_limit - self.current_limit))
        self.current_limit = round(self.current_limit + delta, 3)
        self.limit_set_date = datetime.now()


class OverloadPredictor:
    """
    ML-based risk prediction (DECISION SUPPORT ONLY)
    Does NOT predict capacity or override user judgment
    """
    
    def __init__(self, model_type: str = 'logistic'):
        """
        Args:
            model_type: 'logistic' (default) or 'tree'
                       Both are simple and interpretable
        """
        self.model_type = model_type
        self.scaler = StandardScaler()
        
        if model_type == 'logistic':
            # Logistic Regression: linear, probabilistic, interpretable
            self.model = LogisticRegression(
                random_state=42,
                max_iter=1000,
                penalty='l2',
                C=1.0
            )
        else:
            # Shallow Decision Tree: handles non-linearity, still interpretable
            self.model = DecisionTreeClassifier(
                max_depth=4,
                min_samples_leaf=5,
                random_state=42
            )
        
        self.is_trained = False
        self.feature_names = [
            'planned_load',
            'task_count',
            'high_effort_count',
            'has_deadline',
            'day_of_week',
            'load_to_limit_ratio'
        ]
    
    def _extract_features(self, 
                          planned_load: float,
                          tasks: List[Task],
                          current_limit: Optional[float],
                          date: datetime) -> np.ndarray:
        """Extract features for ML prediction"""
        
        high_effort_count = sum(1 for t in tasks if t.mental_effort == MentalEffort.HIGH)
        has_deadline = any(t.deadline is not None for t in tasks)
        
        # Load to limit ratio (key feature)
        load_to_limit_ratio = (
            planned_load / current_limit if current_limit and current_limit > 0
            else 1.0
        )
        
        features = [
            planned_load,
            len(tasks),
            high_effort_count,
            1 if has_deadline else 0,
            date.weekday(),  # 0=Monday, 6=Sunday
            load_to_limit_ratio
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train(self, history: List[DailyOutcome], current_limit: Optional[float]):
        """Train the overload risk model"""
        
        if len(history) < 15:
            return  # Not enough data
        
        X = []
        y = []
        
        for outcome in history:
            # Reconstruct features from outcome
            load_ratio = (
                outcome.planned_load / current_limit if current_limit and current_limit > 0
                else 1.0
            )
            
            features = [
                outcome.planned_load,
                outcome.task_count,
                outcome.high_effort_count,
                1 if outcome.had_deadline else 0,
                outcome.day_of_week,
                load_ratio
            ]
            
            X.append(features)
            # Target: 1 if failed (overload), 0 if succeeded
            y.append(0 if outcome.success else 1)
        
        X = np.array(X)
        y = np.array(y)

        # Need both classes to fit logistic regression
        if len(set(y)) < 2:
            return

        # Scale features for logistic regression
        if self.model_type == 'logistic':
            X = self.scaler.fit_transform(X)

        self.model.fit(X, y)
        self.is_trained = True
    
    def predict_risk(self,
                     planned_load: float,
                     tasks: List[Task],
                     current_limit: Optional[float],
                     date: datetime = None) -> float:
        """
        Predict probability of overload
        
        Returns:
            Risk score between 0 and 1
            Higher = more likely to overload
        """
        if not self.is_trained:
            return None
        
        if date is None:
            date = datetime.now()
        
        X = self._extract_features(planned_load, tasks, current_limit, date)
        
        if self.model_type == 'logistic':
            X = self.scaler.transform(X)
        
        # Get probability of overload
        risk_prob = self.model.predict_proba(X)[0][1]
        
        return risk_prob
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance for interpretability"""
        if not self.is_trained:
            return {}
        
        if self.model_type == 'logistic':
            # For logistic regression, use coefficient magnitudes
            importance = np.abs(self.model.coef_[0])
        else:
            # For decision tree, use built-in feature importance
            importance = self.model.feature_importances_
        
        # Normalize to sum to 1
        importance = importance / importance.sum()
        
        return {k: float(v) for k, v in zip(self.feature_names, importance)}



class CognitiveTaskPlanner:
    """
    Main system orchestrator
    Combines all components following HCI-ML principles
    """
    
    def __init__(self):
        self.calculator = CognitiveLoadCalculator()
        self.capacity_learner = CapacityLearner()
        self.predictor = OverloadPredictor(model_type='logistic')
        self.today_plan = None
        self.committed_plan_dates: List[str] = []  # ISO date strings, one per commit

        # Nudge thresholds
        self.high_risk_threshold = 0.6
        self.extreme_risk_threshold = 0.8
    
    def plan_day(self, 
                 tasks: List[Task],
                 date: datetime = None) -> Dict:
        """
        Main planning function - analyzes a day's tasks
        
        Returns comprehensive analysis with nudge decision
        """
        if not tasks:
            raise ValueError("tasks list cannot be empty")
        if date is None:
            date = datetime.now()

        # 1. Compute cognitive load (RULE-BASED)
        daily_load = self.calculator.compute_daily_load(tasks)
        breakdown = self.calculator.get_task_breakdown(tasks)
        
        # 2. Get user state and capacity
        user_state = self.capacity_learner.get_user_state()
        current_limit = self.capacity_learner.current_limit
        
        # 3. Get ML risk prediction (model is trained in record_outcome, not here)
        ml_risk = self.predictor.predict_risk(
            daily_load, tasks, current_limit, date
        )

        # 4. NUDGE DECISION LOGIC (Human-in-the-loop)
        should_nudge = False
        nudge_message = None
        nudge_severity = None
        
        if current_limit is not None:
            exceeds_limit = daily_load > current_limit
            high_risk = ml_risk is not None and ml_risk >= self.high_risk_threshold

            if ml_risk is None and exceeds_limit:
                # ML not trained yet — nudge based on raw capacity ratio
                ratio = daily_load / current_limit
                if ratio >= 1.5:
                    should_nudge = True
                    nudge_severity = "warning"
                    nudge_message = (
                        f"This day is {ratio:.0%} of your usual capacity ({current_limit:.1f}). "
                        "Consider trimming some tasks."
                    )
                elif ratio >= 1.2:
                    should_nudge = True
                    nudge_severity = "caution"
                    nudge_message = (
                        f"This is above your usual capacity ({daily_load:.1f} vs {current_limit:.1f}). "
                        "Worth a review."
                    )
            elif exceeds_limit and high_risk:
                should_nudge = True
                if ml_risk >= self.extreme_risk_threshold:
                    nudge_severity = "warning"
                    nudge_message = (
                        f"This day looks quite heavy ({daily_load:.1f} vs your usual {current_limit:.1f}). "
                        f"Consider moving some tasks to another day."
                    )
                else:
                    nudge_severity = "caution"
                    nudge_message = (
                        f"This is above your usual load ({daily_load:.1f} vs {current_limit:.1f}). "
                        "You might want to review your task list."
                    )
        
        # Return comprehensive analysis
        return {
            'daily_load': daily_load,
            'breakdown': breakdown,
            'user_state': user_state.value,
            'current_limit': current_limit,
            'ml_risk_score': ml_risk,
            'ml_available': self.predictor.is_trained,
            'should_nudge': should_nudge,
            'nudge_message': nudge_message,
            'nudge_severity': nudge_severity,
            'feature_importance': self.predictor.get_feature_importance()
        }
    
    def record_outcome(self,
                      date: datetime,
                      tasks: List[Task],
                      completion_rate: float):
        """Record how a planned day actually went"""
        if not 0.0 <= completion_rate <= 1.0:
            raise ValueError("completion_rate must be between 0.0 and 1.0")

        daily_load = self.calculator.compute_daily_load(tasks)
        high_effort_count = sum(1 for t in tasks if t.mental_effort == MentalEffort.HIGH)
        had_deadline = any(t.deadline is not None for t in tasks)

        # Capture limit BEFORE EMA moves it — needed for calibration metrics
        limit_before = self.capacity_learner.current_limit

        outcome = DailyOutcome(
            date=date,
            planned_load=daily_load,
            actual_completion_rate=completion_rate,
            task_count=len(tasks),
            high_effort_count=high_effort_count,
            had_deadline=had_deadline,
            day_of_week=date.weekday(),
            success=completion_rate >= 0.7,
            capacity_limit_at_time=limit_before,
        )

        self.capacity_learner.add_outcome(outcome)
        self.capacity_learner.update_limit(outcome)

        if len(self.capacity_learner.history) >= 15:
            self.predictor.train(
                self.capacity_learner.history,
                self.capacity_learner.current_limit
            )
    
    def get_history(self) -> List[Dict]:
        """Return serializable history for frontend display"""
        result = []
        for h in self.capacity_learner.history:
            d = vars(h).copy()
            d['date'] = h.date.isoformat() if isinstance(h.date, datetime) else h.date
            result.append(d)
        return result

    def log_committed_plan(self, date: datetime):
        """Record that a plan was committed on this date (for engagement rate tracking)."""
        date_str = date.strftime('%Y-%m-%d')
        if date_str not in self.committed_plan_dates:
            self.committed_plan_dates.append(date_str)

    def get_usage_metrics(self) -> Dict:
        """
        Compute four usage/outcome metrics for user study evaluation.

        - overload_rate: fraction of recorded days where completion_rate < 0.7
        - mean_completion_rate: average completion_rate across all recorded days
        - engagement_rate: fraction of committed-plan days that also have a recorded outcome
        - dropout_rate: fraction of days in the study window with no activity at all
        """
        history = self.capacity_learner.history
        n = len(history)

        # Metric 1 — Overload rate
        overload_rate = (
            round(sum(1 for h in history if not h.success) / n, 3)
            if n else None
        )

        # Metric 2 — Mean completion rate
        mean_completion_rate = (
            round(sum(h.actual_completion_rate for h in history) / n, 3)
            if n else None
        )

        # Metric 3 — Engagement rate
        # A committed date "counts" if there is a recorded outcome on any date >= that date
        outcome_dates = {
            (h.date.strftime('%Y-%m-%d') if isinstance(h.date, datetime) else h.date[:10])
            for h in history
        }
        committed = set(self.committed_plan_dates)
        engaged_days = committed & outcome_dates  # dates with both a commit and an outcome
        engagement_rate = (
            round(len(engaged_days) / len(committed), 3)
            if committed else None
        )

        # Metric 4 — Dropout rate
        # Study window: first activity to today (inclusive).
        # Activity = a committed plan OR a recorded outcome on that date.
        active_dates = committed | outcome_dates
        if active_dates:
            first = min(active_dates)
            today = datetime.now().strftime('%Y-%m-%d')
            # Generate all calendar days in the window
            start = datetime.strptime(first, '%Y-%m-%d')
            end   = datetime.strptime(today, '%Y-%m-%d')
            total_days = (end - start).days + 1
            inactive_days = total_days - len({d for d in active_dates if first <= d <= today})
            dropout_rate = round(inactive_days / total_days, 3) if total_days > 0 else None
        else:
            dropout_rate = None
            total_days = 0

        return {
            'days_recorded': n,
            'overload_rate': overload_rate,
            'mean_completion_rate': mean_completion_rate,
            'engagement_rate': engagement_rate,
            'committed_plan_days': len(committed),
            'engaged_days': len(engaged_days) if committed else 0,
            'dropout_rate': dropout_rate,
            'study_window_days': total_days if active_dates else 0,
        }

    def get_calibration_metrics(self) -> Dict:
        """
        Compute the three calibration metrics for user study evaluation.

        Returns:
          - trajectory: capacity_limit per recorded day
          - early_variance / late_variance: EMA convergence (days 1-7 vs 14-20)
          - convergence_ratio: late / early (< 1.0 means tighter calibration)
          - surprise_log: per-day flag for surprising outcomes
          - rolling_surprise_rate: 7-day rolling surprise rate per day
          - overall_surprise_rate: fraction of surprising days overall
        """
        history = self.capacity_learner.history
        n = len(history)

        # Metric 2 — capacity trajectory
        trajectory = [
            {
                'date': h.date.isoformat() if isinstance(h.date, datetime) else h.date,
                'day_number': i + 1,
                'capacity_limit': h.capacity_limit_at_time,
            }
            for i, h in enumerate(history)
            if h.capacity_limit_at_time is not None
        ]

        # Metric 1 — EMA convergence: variance in days 1-7 vs 14-20
        early_limits = [h.capacity_limit_at_time for h in history[:7] if h.capacity_limit_at_time is not None]
        late_limits  = [h.capacity_limit_at_time for h in history[13:20] if h.capacity_limit_at_time is not None]
        early_variance = float(np.var(early_limits)) if len(early_limits) >= 2 else None
        late_variance  = float(np.var(late_limits))  if len(late_limits) >= 2 else None

        # Metric 3 — per-day surprise flag
        surprise_log = []
        for i, h in enumerate(history):
            if h.capacity_limit_at_time is None:
                continue
            over_limit = h.planned_load > h.capacity_limit_at_time
            surprised = (over_limit == h.success)  # True when over+succeed OR under+fail
            surprise_log.append({
                'date': h.date.isoformat() if isinstance(h.date, datetime) else h.date,
                'day_number': i + 1,
                'surprised': surprised,
            })

        # 7-day rolling surprise rate
        rolling_rate = []
        for i in range(len(surprise_log)):
            window = surprise_log[max(0, i - 6): i + 1]
            rate = sum(1 for s in window if s['surprised']) / len(window)
            rolling_rate.append({'day_number': surprise_log[i]['day_number'], 'rate': round(rate, 3)})

        return {
            'days_recorded': n,
            'early_variance': early_variance,
            'late_variance': late_variance,
            'convergence_ratio': (
                round(late_variance / early_variance, 3)
                if early_variance and late_variance and early_variance > 0
                else None
            ),
            'trajectory': trajectory,
            'surprise_log': surprise_log,
            'rolling_surprise_rate': rolling_rate,
            'overall_surprise_rate': (
                round(sum(1 for s in surprise_log if s['surprised']) / len(surprise_log), 3)
                if surprise_log else None
            ),
        }

    def _serialize_outcome(self, outcome: 'DailyOutcome') -> Dict:
        d = vars(outcome).copy()
        d['date'] = outcome.date.isoformat() if isinstance(outcome.date, datetime) else outcome.date
        return d

    def _deserialize_outcome(self, d: Dict) -> 'DailyOutcome':
        d = d.copy()
        if isinstance(d['date'], str):
            d['date'] = datetime.fromisoformat(d['date'])
        d.setdefault('capacity_limit_at_time', None)
        return DailyOutcome(**d)

    def save_state(self, filepath: str):
        """Save system state for persistence"""
        def _dt(v):
            return v.isoformat() if isinstance(v, datetime) else v

        state = {
            'capacity_learner': {
                'history': [self._serialize_outcome(h) for h in self.capacity_learner.history],
                'current_limit': self.capacity_learner.current_limit,
                'limit_set_date': _dt(self.capacity_learner.limit_set_date)
            },
            'today_plan': self.today_plan,
            'committed_plan_dates': self.committed_plan_dates,
        }

        with open(filepath, 'w') as f:
            json.dump(state, f)

        # Save ML model separately
        if self.predictor.is_trained:
            with open(filepath.replace('.json', '_model.pkl'), 'wb') as f:
                pickle.dump({
                    'model': self.predictor.model,
                    'scaler': self.predictor.scaler
                }, f)

    def load_state(self, filepath: str):
        """Load system state"""
        with open(filepath, 'r') as f:
            state = json.load(f)

        def _dt(v):
            return datetime.fromisoformat(v) if isinstance(v, str) else v

        # Restore capacity learner
        self.capacity_learner.history = [
            self._deserialize_outcome(h) for h in state['capacity_learner']['history']
        ]
        self.capacity_learner.current_limit = state['capacity_learner']['current_limit']
        self.capacity_learner.limit_set_date = _dt(state['capacity_learner'].get('limit_set_date'))

        self.today_plan = state.get('today_plan', None)
        self.committed_plan_dates = state.get('committed_plan_dates', [])

        # Load ML model
        try:
            with open(filepath.replace('.json', '_model.pkl'), 'rb') as f:
                model_data = pickle.load(f)
                self.predictor.model = model_data['model']
                self.predictor.scaler = model_data['scaler']
                self.predictor.is_trained = True
        except FileNotFoundError:
            pass


# Example usage
if __name__ == "__main__":
    print("Cognitive Load-Aware Task Planner - Implementation Ready")
    print("=" * 60)
    print("\nKey Components:")
    print("1. CognitiveLoadCalculator - Rule-based cost computation")
    print("2. CapacityLearner - Historical outcome analysis")
    print("3. OverloadPredictor - ML risk estimation (Logistic Regression)")
    print("4. ExplorationManager - Controlled growth mechanism")
    print("5. CognitiveTaskPlanner - Main orchestrator")
    print("\nML Model: Logistic Regression (interpretable, probabilistic)")
    print("Growth Mechanism: Exploration band + user confirmation")
    print("Philosophy: Human-in-the-loop, user agency preserved")
