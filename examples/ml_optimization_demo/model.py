"""ML optimization using Gaussian Process regression."""
import warnings
import mesa
import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
from sklearn.preprocessing import StandardScaler
from .agents import SimpleAgent
warnings.filterwarnings('ignore',category=UserWarning)

class MLDemoModel(mesa.Model):
    """Simple segregation model for testing parameter optimization."""
    def __init__(self,width=20,height=20,num_agents=30,ratio=0.5,
                 exploration_bias=0.5,noise_level=0.05,seed=None):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.num_agents = num_agents
        self.ratio = ratio
        self.exploration_bias = exploration_bias
        self.noise_level = noise_level
        self.grid=mesa.space.MultiGrid(width,height,torus=False)
        self.schedule=mesa.time.RandomActivation(self)
        for i in range(num_agents):
            agent=SimpleAgent(i,self)
            self.schedule.add(agent)
            x=self.random.randrange(width)
            y=self.random.randrange(height)
            self.grid.place_agent(agent,(x,y))
        self.datacollector=mesa.DataCollector(
            model_reporters={
                "Segregation":self.segregation_score,
                "AgentCount":lambda m:len(m.schedule.agents),
            }
        )
    def step(self):
        """Advance model by one step."""
        self.schedule.step()
        self.datacollector.collect(self)
    def segregation_score(self):
        """Count how many neighbors match agent type (0-1 score)."""
        similar=0
        total=0
        for agent in self.schedule.agents:
            neighbors=self.grid.get_neighbors(agent.pos,moore=True)
            for neighbor in neighbors:
                if neighbor.type==agent.type:
                    similar+=1
                total+=1
        base_score=similar/total if total>0 else 0
        noise=self.random.gauss(0,self.noise_level)
        noisy_score=np.clip(base_score+noise,0,1)
        return noisy_score
    def optimize_parameters(self,n_iterations=30):
        """Try random parameters then use ML to find better ones."""
        X=[]
        y=[]
        phase=[]
        print("\nPhase 1: Random exploration (10 samples)")
        for i in range(10):
            params={
                "num_agents":self.random.randint(10,60),
                "ratio":self.random.uniform(0.3,0.8),
                "exploration_bias":self.random.uniform(0.0,1.0),
            }
            model = MLDemoModel(
                width=self.width, height=self.height, **params, seed=None
            )
            for _ in range(100):
                model.step()
            score = model.segregation_score()
            X.append([params["num_agents"], params["ratio"], params["exploration_bias"]])
            y.append(score)
            phase.append(1)
            print(f"  {i+1:2d}. agents={params['num_agents']:2d}, "
                  f"ratio={params['ratio']:.2f}, "
                  f"bias={params['exploration_bias']:.2f} score={score:.4f}")
        best_score = max(y)
        best_idx = np.argmax(y)
        best_params={
            "num_agents":int(X[best_idx][0]),
            "ratio":float(X[best_idx][1]),
            "exploration_bias":float(X[best_idx][2]),
        }
        print("\nPhase 2: Bayesian Optimization (20 iterations)")
        kernel=RBF(length_scale=1.0,length_scale_bounds=(1e-2,1e3))
        gp=GaussianProcessRegressor(
            kernel=kernel,random_state=42,n_restarts_optimizer=10
        )
        scaler = StandardScaler()
        X_normalized = scaler.fit_transform(X)
        for i in range(20):
            gp.fit(X_normalized,y)
            candidates = []
            for _ in range(100):
                num=self.random.randint(10,60)
                ratio=self.random.uniform(0.3,0.8)
                bias=self.random.uniform(0.0,1.0)
                candidates.append([num,ratio,bias])
            candidates_normalized=scaler.transform(candidates)
            preds,stds=gp.predict(candidates_normalized,return_std=True)
            ucb=preds+1.96*stds
            best_candidate_idx=np.argmax(ucb)
            params={
                "num_agents":int(candidates[best_candidate_idx][0]),
                "ratio":float(candidates[best_candidate_idx][1]),
                "exploration_bias":float(candidates[best_candidate_idx][2]),
            }
            model = MLDemoModel(
                width=self.width, height=self.height, **params, seed=None
            )
            for _ in range(100):
                model.step()
            score = model.segregation_score()
            X.append([params["num_agents"], params["ratio"], params["exploration_bias"]])
            y.append(score)
            phase.append(2)
            if score > best_score:
                best_score = score
                best_params = params
                print(f"  {i+1:2d}. NEW BEST - agents={params['num_agents']:2d}, "
                      f"ratio={params['ratio']:.2f}, "
                      f"bias={params['exploration_bias']:.2f}, score={score:.4f}")
            else:
                print(f"  {i+1:2d}. agents={params['num_agents']:2d}, "
                      f"ratio={params['ratio']:.2f}, "
                      f"bias={params['exploration_bias']:.2f}, score={score:.4f}")
            X_normalized=scaler.fit_transform(X)
        print("\nOptimization Results")
        y=np.array(y)
        phase=np.array(phase)
        random_scores=y[phase==1]
        ml_scores=y[phase==2]
        print("\nPhase 1 (Random Search):")
        print(f"  Best: {np.max(random_scores):.4f}")
        print(f"  Mean: {np.mean(random_scores):.4f} +/- {np.std(random_scores):.4f}")
        print("\nPhase 2 (Bayesian Optimization):")
        print(f"  Best: {np.max(ml_scores):.4f}")
        print(f"  Mean: {np.mean(ml_scores):.4f} +/- {np.std(ml_scores):.4f}")
        improvement_pct=((best_score-np.max(random_scores))/np.max(random_scores)*100)
        print(f"\nImprovement: {improvement_pct:+.2f}%")
        print("\nBest Parameters:")
        print(f"  agents: {best_params['num_agents']}")
        print(f"  ratio: {best_params['ratio']:.4f}")
        print(f"  exploration_bias: {best_params['exploration_bias']:.4f}")
        print(f"  score: {best_score:.4f}\n")
        return {
            "best_params":best_params,
            "best_score":best_score,
            "all_scores":y.tolist(),
            "all_phases":phase.tolist(),
            "random_scores":random_scores.tolist(),
            "ml_scores":ml_scores.tolist(),
        }

def visualize_optimization(result,save_path=None):
    """Plot the optimization results."""
    all_scores=np.array(result["all_scores"])
    phases=np.array(result["all_phases"])
    fig,axes=plt.subplots(1,2,figsize=(14,5))
    ax=axes[0]
    random_idx=phases==1
    ml_idx=phases==2
    ax.scatter(np.where(random_idx)[0],all_scores[random_idx], 
               color='red', s=100, alpha=0.6, label='Random Search', marker='o')
    ax.scatter(np.where(ml_idx)[0],all_scores[ml_idx], 
               color='blue', s=100, alpha=0.6, label='Bayesian Opt', marker='s')
    ax.set_xlabel('Iteration',fontsize=12,fontweight='bold')
    ax.set_ylabel('Score',fontsize=12,fontweight='bold')
    ax.set_title('Optimization Performance: Random vs Bayesian',fontsize=13,fontweight='bold')
    ax.grid(True,alpha=0.3)
    ax.legend(fontsize=11)
    ax=axes[1]
    running_best_random=np.maximum.accumulate(all_scores[random_idx])
    running_best_ml=np.maximum.accumulate(all_scores[ml_idx])
    ax.plot(range(len(running_best_random)),running_best_random, 
            'o-',color='red',linewidth=2,markersize=6,label='Random Search')
    ax.plot(range(len(running_best_random), len(running_best_random)+len(running_best_ml)), 
            running_best_ml, 's-', color='blue', linewidth=2, markersize=6, label='Bayesian Opt')
    ax.axvline(x=10,color='gray',linestyle='--',alpha=0.5,linewidth=1)
    ax.text(5,ax.get_ylim()[1]*0.95,'Phase 1',ha='center',fontsize=10,style='italic')
    ax.text(20,ax.get_ylim()[1]*0.95,'Phase 2',ha='center',fontsize=10,style='italic')
    ax.set_xlabel('Iteration',fontsize=12,fontweight='bold')
    ax.set_ylabel('Best Score Found',fontsize=12,fontweight='bold')
    ax.set_title('Convergence: Best Score Over Time',fontsize=13,fontweight='bold')
    ax.grid(True,alpha=0.3)
    ax.legend(fontsize=11)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path,dpi=300,bbox_inches='tight')
        print(f"Visualization saved to: {save_path}")
    plt.show()

def run_statistical_validation(num_runs=15):
    """Run it multiple times and see if results are consistent."""
    print(f"\nRunning {num_runs} optimization runs...\n")
    all_improvements = []
    all_best_scores = []
    for run in range(num_runs):
        print(f"Run {run+1}/{num_runs}...", end=" ", flush=True)
        model = MLDemoModel()
        result = model.optimize_parameters()
        random_best=max(result["random_scores"])
        improvement=((result["best_score"]-random_best)/random_best*100)
        all_improvements.append(improvement)
        all_best_scores.append(result["best_score"])
        print(f"improvement: {improvement:+.2f}%")
    consistency=sum(1 for x in all_improvements if x>=0)/num_runs*100
    print("\nStatistical Summary:")
    print(f"  Mean improvement: {np.mean(all_improvements):+.2f}%")
    print(f"  Std deviation: {np.std(all_improvements):.2f}%")
    print(f"  Min: {np.min(all_improvements):+.2f}%")
    print(f"  Max: {np.max(all_improvements):+.2f}%")
    print(f"  Consistency: {consistency:.1f}% of runs beat random search\n")
    return {
        "improvements":all_improvements,
        "best_scores":all_best_scores,
        "mean_improvement":np.mean(all_improvements),
        "std_improvement":np.std(all_improvements),
        "consistency":consistency,
    }

def run_optimization():
    """Run one optimization and show the plot."""
    model = MLDemoModel()
    result = model.optimize_parameters()
    visualize_optimization(result)
    return result

def run_full_analysis(num_runs=15):
    """Run multiple times then show a plot from the final run."""
    stats=run_statistical_validation(num_runs=num_runs)
    print("Creating visualization from final run...")
    model = MLDemoModel()
    result = model.optimize_parameters()
    visualize_optimization(result)
    
    return stats, result


if __name__ == "__main__":
    # Full analysis with 15 runs
    stats,final_result=run_full_analysis(num_runs=15)