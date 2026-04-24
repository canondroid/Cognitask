"""
Simplified Demo for Cognitive Load-Aware Task Planner
Shows core functionality without complex edge cases
"""

from cognitive_task_planner import (
    CognitiveTaskPlanner,
    Task,
    MentalEffort
)
from datetime import datetime, timedelta
import numpy as np


def safe_format_limit(limit):
    """Safely format limit value"""
    return f"{limit:.2f}" if limit is not None else "Not set"


def demo_1_basic_planning():
    """Demo 1: Basic task planning"""
    print("\n" + "="*70)
    print("DEMO 1: Basic Task Planning (New User)")
    print("="*70)
    
    planner = CognitiveTaskPlanner()
    
    # Create tasks for today
    tasks = [
        Task("Check emails", MentalEffort.LOW, 30),
        Task("Team meeting", MentalEffort.LOW, 60),
        Task("Code implementation", MentalEffort.MEDIUM, 90),
        Task("System design", MentalEffort.HIGH, 120),
        Task("Code review", MentalEffort.MEDIUM, 45)
    ]
    
    result = planner.plan_day(tasks)
    
    print(f"\n📊 Task Analysis:")
    print(f"   Total Cognitive Load: {result['daily_load']:.2f}")
    print(f"   Total Time: {result['breakdown']['total_time_minutes']} minutes")
    print(f"   User State: {result['user_state']}")
    
    print(f"\n📋 Effort Distribution:")
    dist = result['breakdown']['effort_distribution']
    print(f"   Low: {dist['low']} tasks")
    print(f"   Medium: {dist['medium']} tasks")
    print(f"   High: {dist['high']} tasks")
    
    print(f"\n⚡ Individual Task Costs:")
    for name, cost in result['breakdown']['task_costs']:
        print(f"   {name}: {cost:.2f}")
    
    if result['should_nudge']:
        print(f"\n⚠️  Warning: {result['nudge_message']}")
    else:
        print(f"\n✅ Your plan looks manageable!")


def demo_2_with_history():
    """Demo 2: System with learning history"""
    print("\n" + "="*70)
    print("DEMO 2: Learning from History")
    print("="*70)
    
    planner = CognitiveTaskPlanner()
    np.random.seed(42)
    
    # Build 25 days of history
    print("\n🔄 Simulating 25 days of work...")
    for day in range(25):
        date = datetime.now() - timedelta(days=25-day)
        
        # Create varied tasks
        num_tasks = np.random.randint(3, 6)
        tasks = []
        for i in range(num_tasks):
            effort = np.random.choice(
                [MentalEffort.LOW, MentalEffort.MEDIUM, MentalEffort.HIGH],
                p=[0.3, 0.5, 0.2]
            )
            duration = np.random.randint(30, 90)
            tasks.append(Task(f"Task_{i}", effort, duration))
        
        # Plan and record
        result = planner.plan_day(tasks, date)
        load = result['daily_load']
        
        # Simulate completion (realistic based on load)
        if load < 6:
            completion = np.random.uniform(0.8, 1.0)
        elif load < 9:
            completion = np.random.uniform(0.65, 0.9)
        else:
            completion = np.random.uniform(0.4, 0.7)
        
        planner.record_outcome(date, tasks, completion)
    
    # Show what was learned
    print(f"✅ History built: {len(planner.capacity_learner.history)} days")
    limit = planner.capacity_learner.current_limit
    print(f"📈 Learned Capacity: {safe_format_limit(limit)}")
    print(f"🎯 User State: {planner.capacity_learner.get_user_state().value}")
    
    # Now test a new day
    print("\n" + "-"*70)
    print("Planning a new day with learned capacity:")
    print("-"*70)
    
    new_tasks = [
        Task("Design meeting", MentalEffort.MEDIUM, 90),
        Task("Implementation", MentalEffort.HIGH, 120),
        Task("Code review", MentalEffort.MEDIUM, 60),
        Task("Documentation", MentalEffort.LOW, 45)
    ]
    
    result = planner.plan_day(new_tasks)
    
    print(f"\n📊 Load: {result['daily_load']:.2f}")
    print(f"📏 Your Capacity: {safe_format_limit(result['current_limit'])}")
    print(f"🎲 ML Risk Score: {result['ml_risk_score']:.1%}")
    
    if result['should_nudge']:
        print(f"\n⚠️  {result['nudge_severity'].upper()}: {result['nudge_message']}")
    elif result['exploration_allowed']:
        print(f"\n💪 You're in your growth zone - challenge accepted!")
    else:
        print(f"\n✅ This looks good for you!")
    
    # Show ML insights
    if result['feature_importance']:
        print(f"\n🔍 Top Risk Factors:")
        importance = result['feature_importance']
        for feature, value in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"   {feature}: {value:.1%}")


def demo_3_ml_explanation():
    """Demo 3: Understanding the ML model"""
    print("\n" + "="*70)
    print("DEMO 3: ML Model Explanation")
    print("="*70)
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║                   MACHINE LEARNING MODEL DETAILS                 ║
╠════════════════════════════════════════════════════════════════╣
║                                                                  ║
║ Model Type: Logistic Regression                                 ║
║                                                                  ║
║ Why Logistic Regression?                                        ║
║   ✓ Interpretable (can see feature weights)                    ║
║   ✓ Probabilistic (gives risk scores 0-100%)                   ║
║   ✓ Works with small data (15-20 samples)                      ║
║   ✓ Computationally efficient                                   ║
║   ✓ No overfitting risk                                         ║
║                                                                  ║
║ What does it predict?                                           ║
║   → P(overload | features)                                      ║
║   → Risk score between 0 and 1                                  ║
║                                                                  ║
║ Input Features:                                                 ║
║   1. planned_load         - Total cognitive load                ║
║   2. task_count           - Number of tasks                     ║
║   3. high_effort_count    - Number of HIGH effort tasks         ║
║   4. has_deadline         - Any deadlines today?                ║
║   5. day_of_week          - Monday=0, Sunday=6                  ║
║   6. load_to_limit_ratio  - Load / Your usual capacity          ║
║                                                                  ║
║ Output:                                                         ║
║   Risk score (0.0 to 1.0)                                       ║
║   → Low risk:   < 0.4                                           ║
║   → Medium risk: 0.4 - 0.6                                      ║
║   → High risk:  0.6 - 0.8                                       ║
║   → Extreme:    > 0.8                                           ║
║                                                                  ║
║ Alternative Model: Decision Tree (max_depth=4)                  ║
║   Can be used instead if non-linear patterns are important      ║
║                                                                  ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚙️  SYSTEM ARCHITECTURE:")
    print("""
    1. [USER INPUT]
       ↓ Mental Effort + Duration
       
    2. [RULE-BASED CALCULATOR]
       ↓ Task Cost = Effort × (1 + 0.25 × Duration/60)
       ↓ Daily Load = Σ(Task Costs)
       
    3. [CAPACITY LEARNER - Rule-based]
       ↓ Analyzes historical outcomes
       ↓ Finds highest load with 70% success rate
       
    4. [ML PREDICTOR - Logistic Regression]
       ↓ Estimates P(overload | features)
       ↓ Provides risk score
       
    5. [NUDGE DECISION - Hybrid]
       ↓ IF (Load > Limit) AND (ML Risk High):
       ↓    Show warning
       ↓ ELIF exploration zone:
       ↓    Allow growth attempt
       ↓ ELSE:
       ↓    Stay silent
       
    6. [USER SEES]
       → Nudge/encouragement/nothing
       → Makes informed decision
    """)


def demo_4_growth_mechanism():
    """Demo 4: How growth works"""
    print("\n" + "="*70)
    print("DEMO 4: Controlled Growth Mechanism")
    print("="*70)
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║                    GROWTH MECHANISM EXPLAINED                    ║
╠════════════════════════════════════════════════════════════════╣
║                                                                  ║
║ Problem: Without growth, users get "frozen" at their initial    ║
║          capacity and can never improve.                        ║
║                                                                  ║
║ Solution: Controlled Exploration Windows                        ║
║                                                                  ║
║ Exploration Band:                                               ║
║   [Your Limit, Your Limit + 0.5]                                ║
║                                                                  ║
║   Example: If your limit is 7.0, exploration is 7.0-7.5         ║
║                                                                  ║
║ Rules for Exploration:                                          ║
║   ✓ Must be stable at current limit for 7+ days                 ║
║   ✓ No recent failures                                          ║
║   ✓ ML predicts risk < 80% (not extreme)                        ║
║   ✓ Within exploration band                                     ║
║                                                                  ║
║ In Exploration Zone:                                            ║
║   → Nudges are suppressed                                       ║
║   → Encouraging message shown                                   ║
║   → Outcomes tracked separately                                 ║
║                                                                  ║
║ After Successful Exploration (5+ successes):                    ║
║   System asks: "You've been handling heavier days well.         ║
║                 Treat this as your new normal?"                 ║
║                                                                  ║
║   User options:                                                 ║
║   ✓ Accept → Limit increases by 0.5                             ║
║   ✗ Decline → Nothing changes                                   ║
║   ⏰ Ask later → Preserves agency                                ║
║                                                                  ║
║ Safety Limits:                                                  ║
║   • Max 0.5 increase per suggestion                             ║
║   • Max 1.0 increase per week                                   ║
║   • Always requires user confirmation                           ║
║                                                                  ║
╚════════════════════════════════════════════════════════════════╝
    """)


def demo_5_comparison():
    """Demo 5: What makes this approach good"""
    print("\n" + "="*70)
    print("DEMO 5: Why This Approach Works (HCI + ML)")
    print("="*70)
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║              GOOD HCI-ML DESIGN vs COMMON MISTAKES               ║
╠════════════════════════════════════════════════════════════════╣
║                                                                  ║
║ ✅ THIS SYSTEM DOES:                                             ║
║                                                                  ║
║  1. Respects User Intent                                        ║
║     → Mental effort is USER-DEFINED                             ║
║     → System never overrides user labels                        ║
║                                                                  ║
║  2. Transparent Calculations                                    ║
║     → Cost = Effort × DurationModifier (simple formula)         ║
║     → No black boxes                                            ║
║                                                                  ║
║  3. ML as Decision Support Only                                 ║
║     → ML predicts RISK, not capacity                            ║
║     → Humans make final decisions                               ║
║                                                                  ║
║  4. Enables Growth                                              ║
║     → Exploration windows prevent freezing                      ║
║     → User confirmation required                                ║
║                                                                  ║
║  5. Interpretable ML                                            ║
║     → Logistic Regression (not deep learning)                   ║
║     → Can see feature importance                                ║
║                                                                  ║
║ ❌ COMMON MISTAKES (That We Avoided):                            ║
║                                                                  ║
║  1. "ML predicts task difficulty"                               ║
║     → Disempowers users                                         ║
║     → Can't learn user preferences                              ║
║                                                                  ║
║  2. "Auto-schedule everything"                                  ║
║     → Removes user agency                                       ║
║     → Users lose control                                        ║
║                                                                  ║
║  3. "Deep neural network"                                       ║
║     → Black box                                                 ║
║     → Needs tons of data                                        ║
║     → Can't explain decisions                                   ║
║                                                                  ║
║  4. "Fixed capacity threshold"                                  ║
║     → Users can't improve                                       ║
║     → Growth blocked                                            ║
║                                                                  ║
║  5. "Always nudge if ML says high risk"                         ║
║     → Annoying                                                  ║
║     → Ignores exploration needs                                 ║
║                                                                  ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n🎯 KEY PRINCIPLES:")
    principles = [
        "Mental effort is user-defined and respected",
        "Time amplifies effort, but never dominates it",
        "ML supports decisions, it does not make them",
        "Users must be allowed to grow, not frozen by safety"
    ]
    
    for i, principle in enumerate(principles, 1):
        print(f"   {i}. {principle}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("COGNITIVE LOAD-AWARE TASK PLANNER")
    print("Complete Implementation & Demo")
    print("="*70)
    
    # Run demos
    demo_1_basic_planning()
    demo_2_with_history()
    demo_3_ml_explanation()
    demo_4_growth_mechanism()
    demo_5_comparison()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETE!")
    print("="*70)
    
    print("\n📚 Next Steps for Your Project:")
    print("   1. Review cognitive_task_planner.py for implementation")
    print("   2. Understand the ML model (Logistic Regression)")
    print("   3. Test with your own scenarios")
    print("   4. Build a simple UI (web/mobile)")
    print("   5. Collect real user data for evaluation")
    print("   6. Measure HCI metrics (satisfaction, growth rate, etc.)")
    
    print("\n💡 Files Generated:")
    print("   • cognitive_task_planner.py - Main implementation")
    print("   • demo_simple.py - This demo file")
    print("   • planner_state.json - Saved state (if run)")
