import dspy
from sklearn.model_selection import GridSearchCV
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

class HyperparameterTuner:
    def __init__(self):
        self.results_dir = os.path.join(os.path.dirname(__file__), 'tuning_results')
        os.makedirs(self.results_dir, exist_ok=True)
        
    def tune_hyperparameters(self, param_grid):
        """Run real hyperparameter tuning"""
        from sklearn.model_selection import GridSearchCV
        
        # Create parameter combinations
        param_combinations = [
            {
                'learning_rate': lr,
                'batch_size': bs,
                'temperature': temp
            }
            for lr in param_grid['learning_rate']
            for bs in param_grid['batch_size']
            for temp in param_grid['temperature']
        ]
        
        results = {
            'scores': [],
            'best_params': None,
            'best_score': float('-inf')
        }
        
        # Test each combination
        for params in param_combinations:
            # Configure model with current parameters
            dspy.configure(
                lm='gpt-4',
                temperature=params['temperature']
            )
            
            # Create fresh model instance
            from poker_bot.poker_agent import PokerAgent
            model = PokerAgent()
            
            # Train and evaluate
            train_data, valid_data = self._generate_validation_data()
            score = self._evaluate_parameters(model, train_data, valid_data, params)
            
            results['scores'].append({
                'params': params,
                'score': score
            })
            
            # Update best parameters
            if score > results['best_score']:
                results['best_score'] = score
                results['best_params'] = params
        
        # Save results
        results_path = os.path.join(self.results_dir, 'tuning_results.json')
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

    def _generate_validation_data(self):
        """Generate diverse poker scenarios for validation"""
        from itertools import product
        
        positions = ['BTN', 'CO', 'MP', 'UTG', 'BB', 'SB']
        stack_sizes = [1000, 2000, 5000]
        pot_sizes = [100, 200, 500]
        
        scenarios = []
        
        for pos, stack, pot in product(positions, stack_sizes, pot_sizes):
            scenarios.append({
                'hand': 'AH KH',  # Example premium hand
                'table_cards': '',
                'position': pos,
                'pot_size': pot,
                'stack_size': stack,
                'opponent_stack': stack,
                'game_type': 'cash',
                'opponent_tendency': 'unknown'
            })
            
            scenarios.append({
                'hand': '7H 6H',  # Example speculative hand
                'table_cards': '',
                'position': pos,
                'pot_size': pot,
                'stack_size': stack,
                'opponent_stack': stack,
                'game_type': 'cash',
                'opponent_tendency': 'unknown'
            })
        
        # Split into train/valid
        split = int(len(scenarios) * 0.8)
        return scenarios[:split], scenarios[split:]

    def _evaluate_parameters(self, model, train_data, valid_data, params):
        """Evaluate a parameter combination"""
        # Train for a few epochs
        for _ in range(3):  # Quick evaluation with 3 epochs
            for i in range(0, len(train_data), params['batch_size']):
                batch = train_data[i:i + params['batch_size']]
                # Train on batch
                for game in batch:
                    model(
                        hand=game['hand'],
                        table_cards=game['table_cards'],
                        position=game['position'],
                        pot_size=game['pot_size'],
                        stack_size=game['stack_size'],
                        opponent_stack=game['opponent_stack'],
                        game_type=game['game_type'],
                        opponent_tendency=game['opponent_tendency']
                    )
        
        # Evaluate on validation data
        from poker_bot.trainer import PokerEvaluator
        evaluator = PokerEvaluator()
        metrics = evaluator.evaluate(model, valid_data)
        
        # Return composite score
        return (
            metrics['win_rate'] * 0.4 +
            metrics['expected_value'] * 0.3 +
            metrics['decision_quality'] * 0.2 +
            metrics['bluff_efficiency'] * 0.1
        )
    
    def plot_results(self, results):
        """Generate visualization of tuning results"""
        plt.figure(figsize=(10, 6))
        
        # Plot learning rate vs accuracy
        plt.subplot(1, 2, 1)
        sns.lineplot(x=results['learning_rate'], y=results['accuracy'])
        plt.xlabel('Learning Rate')
        plt.ylabel('Accuracy')
        plt.title('Learning Rate Impact')
        
        # Plot batch size vs accuracy 
        plt.subplot(1, 2, 2)
        sns.lineplot(x=results['batch_size'], y=results['accuracy'])
        plt.xlabel('Batch Size')
        plt.ylabel('Accuracy')
        plt.title('Batch Size Impact')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.results_dir, 'tuning_plot.png')
        plt.savefig(plot_path)
        plt.close()
import os
import json
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("Warning: matplotlib or seaborn not installed. Plotting functionality will be disabled.")

class HyperparameterTuner:
    def __init__(self):
        self.results_dir = os.path.join(os.path.dirname(__file__), 'tuning_results')
        os.makedirs(self.results_dir, exist_ok=True)

    def tune_hyperparameters(self, param_grid):
        """Run real hyperparameter tuning"""
        from poker_bot.poker_agent import PokerAgent
        from poker_bot.trainer import PokerEvaluator
        from sklearn.model_selection import ParameterGrid
        import json
        
        train_data, valid_data = self._generate_validation_data()
        evaluator = PokerEvaluator()
        results = []
        
        parameter_list = list(ParameterGrid(param_grid))
        
        for params in parameter_list:
            # Configure DSPy with current parameters
            dspy.configure(
                lm='gpt-4-mini',
                temperature=params['temperature'],
                max_tokens=params['max_tokens']
            )
            
            # Update training configuration
            config = TrainingConfig(
                learning_rate=params['learning_rate'],
                batch_size=params['batch_size'],
                temperature=params['temperature']
            )
            
            # Initialize agent and trainer
            model = PokerAgent()
            trainer = PokerTrainer()
            trainer.agent = model
            trainer.config = config
            
            # Train model briefly for evaluation
            trainer.train_one_epoch(train_data)
            
            # Evaluate model
            metrics = evaluator.evaluate(model, valid_data)
            score = metrics['win_rate']  # Use win rate as the main score
            
            # Save results
            results.append({
                'params': params,
                'metrics': metrics,
                'score': score
            })
        
        # Identify best parameters
        best_result = max(results, key=lambda x: x['score'])
        
        # Save all tuning results to folder
        tuning_results_path = os.path.join(self.results_dir, 'tuning_results.json')
        with open(tuning_results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save best parameters separately
        best_params_path = os.path.join(self.results_dir, 'best_params.json')
        with open(best_params_path, 'w') as f:
            json.dump(best_result, f, indent=2)
        
        print(f"Hyperparameter tuning complete. Best parameters saved to {best_params_path}")
        return best_result

    def plot_results(self, results):
        """Plot tuning results"""
        if not HAS_PLOTTING:
            print("Cannot create plot: matplotlib or seaborn not installed")
            return

        try:
            plt.figure(figsize=(10, 6))
            
            # Extract scores and parameters
            scores = [r['score'] for r in results['scores']]
            params = [f"lr={r['params']['learning_rate']}\nb={r['params']['batch_size']}" 
                     for r in results['scores']]
            
            # Create bar plot
            plt.bar(range(len(scores)), scores)
            plt.xticks(range(len(scores)), params, rotation=45)
            plt.ylabel('Score')
            plt.title('Hyperparameter Tuning Results')
            
            # Add value labels on top of bars
            for i, score in enumerate(scores):
                plt.text(i, score, f'{score:.3f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Save plot
            plot_path = os.path.join(self.results_dir, 'tuning_plot.png')
            plt.savefig(plot_path)
            plt.close()
            
        except Exception as e:
            print(f"Error creating plot: {str(e)}")
