import random
import json
import math
from pathlib import Path

class QuestionGenerator:
    def __init__(self):
        self.user_stats = {
            'math_attempted': 0,
            'math_correct': 0,
            'space_attempted': 0,
            'space_correct': 0,
            'physics_attempted': 0,
            'physics_correct': 0,
            'logic_attempted': 0,
            'logic_correct': 0
        }
        
        # Initialize with default questions if files not found
        self.math_problems = self._load_data('math') or [
            ("What is 15% of 200?", "30", "math"),
            ("Solve for x: 2x + 5 = 15", "5", "math"),
            ("What is the area of a circle with radius 5?", "78.54", "math")
        ]
        
        self.space_facts = self._load_data('space') or [
            ("Which planet has the most moons?", "Saturn", "space"),
            ("How long is a day on Venus in Earth days?", "243", "space"),
            ("What is the hottest planet in our solar system?", "Venus", "space")
        ]
        
        self.physics_concepts = self._load_data('physics') or [
            ("What is the speed of light in vacuum in m/s?", "299792458", "physics"),
            ("Who developed the theory of relativity?", "Einstein", "physics"),
            ("Which law states that F = ma?", "Newton's Second Law", "physics")
        ]
        
        self.logic_puzzles = self._load_data('logic') or [
            ("I speak without a mouth and hear without ears. What am I?", "Echo", "logic"),
            ("What comes once in a minute, twice in a moment, but never in a thousand years?", "M", "logic"),
            ("The more you take, the more you leave behind. What am I?", "Footsteps", "logic")
        ]

    def _load_data(self, category):
        try:
            path = Path(__file__).parent / f'{category}_questions.json'
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def generate_question(self, difficulty='medium'):
        """Generate a question dictionary with question, answer, and category"""
        question_types = ['math', 'space', 'physics', 'logic']
        weights = [
            1 - self._get_accuracy('math'),
            1 - self._get_accuracy('space'),
            1 - self._get_accuracy('physics'), 
            1 - self._get_accuracy('logic')
        ]
        
        # Normalize weights
        total = sum(weights)
        weights = [w/total for w in weights] if total > 0 else None
        
        category = random.choices(question_types, weights=weights or None)[0]
        
        if category == 'math':
            q, a, c = random.choice(self.math_problems)
        elif category == 'space':
            q, a, c = random.choice(self.space_facts)
        elif category == 'physics':
            q, a, c = random.choice(self.physics_concepts)
        else:
            q, a, c = random.choice(self.logic_puzzles)
            
        return {
            "question": q,
            "answer": a,
            "category": c
        }

    def _get_accuracy(self, category):
        attempted = self.user_stats.get(f'{category}_attempted', 0)
        correct = self.user_stats.get(f'{category}_correct', 0)
        return correct / attempted if attempted > 0 else 0

    def check_answer(self, user_answer, correct_answer, category):
        """Check if answer is correct and update stats"""
        self.user_stats[f'{category}_attempted'] += 1
        
        # Normalize answers
        user_norm = str(user_answer).strip().lower()
        correct_norm = str(correct_answer).strip().lower()
        
        # Check for exact match
        if user_norm == correct_norm:
            self.user_stats[f'{category}_correct'] += 1
            return True
            
        # Check for numeric similarity
        try:
            if math.isclose(float(user_norm), float(correct_norm), rel_tol=0.01):
                self.user_stats[f'{category}_correct'] += 1
                return True
        except ValueError:
            pass
            
        return False