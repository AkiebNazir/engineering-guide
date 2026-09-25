# Weights & Biases (WandB) Mastery: Deep Learning Tracking

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* In Guide 23, we learned MLflow is great for saving models and deploying them. But if you are training a massive <abbr title="Large Language Model">LLM</abbr> on 8 GPUs for 3 weeks, MLflow's UI is too basic. You need to watch the Loss curve update live, monitor GPU temperatures so the server doesn't melt, and compare 50 different training runs overlaid on the same graph. **Weights & Biases (WandB)** is the industry standard for this.

**What is it?**
WandB is a developer-first MLOps platform heavily focused on the **Experiment Tracking** phase of Deep Learning. It acts as a cloud-based dashboard for your training loops.

**Why does it exist?**
Before WandB, researchers used TensorBoard, which was clunky and ran locally, making it impossible to share results with teammates. WandB streams all your metrics, system hardware data, and even sample output images directly to a beautiful, collaborative web dashboard in real-time. OpenAI, Anthropic, and Meta all use WandB.

---

## 2. Setup & Installation

You will need a free account at wandb.ai to get an <abbr title="Application Programming Interface">API</abbr> key.

```bash
pip install wandb
```

```python
import wandb

# This will prompt you to paste your API key in the terminal
# wandb.login() 
```

---

## 3. The "Hello World": Tracking a Run

Let's imagine the standard PyTorch training loop from Guide 05. We will inject WandB into it.

### Parameter Breakdown: `wandb.init(...)`
- `project` (str): The high-level folder (e.g., "Llama3-Finetuning"). All runs inside this project will be graphed together automatically!
- `config` (dict): The dictionary of all your hyper-parameters (Learning Rate, Batch Size, etc.). 
  - *Effect:* WandB saves this config forever. In 6 months, you can look at the dashboard, sort all your runs by "Learning Rate", and instantly see which learning rate produced the lowest loss!

```python
import wandb
import random
import time

# 1. Initialize the run
# This creates a URL where you can watch the training live!
run = wandb.init(
    project="My_First_Neural_Network",
    config={
        "learning_rate": 0.01,
        "epochs": 10,
        "batch_size": 32,
        "architecture": "CNN"
    }
)

# 2. Simulate a PyTorch Training Loop
epochs = wandb.config.epochs

for epoch in range(epochs):
    # Simulate the model learning (loss goes down, accuracy goes up)
    fake_loss = 10.0 / (epoch + 1) + random.uniform(0, 1)
    fake_acc = 1.0 - (1.0 / (epoch + 1)) + random.uniform(-0.05, 0.05)
    
    # 3. Log the Metrics!
    # WandB will automatically draw a line chart for 'loss' and 'accuracy'
    wandb.log({
        "epoch": epoch,
        "loss": fake_loss,
        "accuracy": fake_acc
    })
    
    time.sleep(1) # Simulate training time

# 4. End the run
wandb.finish()
```

---

## 4. Deep Dive: Sweeps (Hyperparameter Optimization)

In Scikit-Learn (Guide 03), we used `GridSearchCV` to try every possible combination of hyperparameters. In Deep Learning, training a model takes 3 days. You cannot afford to try 100 combinations. You must use **Bayesian Optimization**. WandB calls this a **Sweep**.

### Parameter Breakdown: The Sweep Config
- `method`: 
  - *`grid`*: Tries every single combination (Slowest).
  - *`random`*: Tries random combinations (Okay).
  - *`bayes`*: The Pro choice. It uses a Gaussian Process math model. It trains a few random runs, looks at the results, and mathematically calculates exactly where the optimal learning rate is likely to be, saving you massive amounts of time and compute costs.
- `metric`: What is the optimizer trying to maximize or minimize? (e.g., maximize `val_accuracy`).

```python
# 1. Define the Sweep Dictionary
sweep_config = {
    'method': 'bayes', # Use AI to find the best AI parameters!
    'metric': {
        'name': 'val_loss',
        'goal': 'minimize'   
    },
    'parameters': {
        'learning_rate': {
            'distribution': 'log_uniform_values',
            'min': 1e-5,
            'max': 1e-2
        },
        'batch_size': {
            'values': [16, 32, 64]
        }
    }
}

# 2. Initialize the Sweep on the WandB Cloud
# sweep_id = wandb.sweep(sweep_config, project="Sweep_Optimization_Project")

# 3. Define the training function
def train_function():
    # WandB will automatically inject the specific parameters for this run!
    with wandb.init() as run:
        lr = wandb.config.learning_rate
        bs = wandb.config.batch_size
        
        # ... Run PyTorch training using 'lr' and 'bs' ...
        # wandb.log({"val_loss": actual_loss})

# 4. Start the Agent!
# It will run the training function 20 times, dynamically picking the best parameters!
# wandb.agent(sweep_id, train_function, count=20)
```

---

## 5. Pro Feature: Artifacts (Data Versioning)

Code is only half of Machine Learning. If your code is versioned in GitHub, but your 50GB image dataset changes on your hard drive, your experiment is no longer reproducible.

WandB **Artifacts** track datasets and models exactly like Git tracks code.

```python
with wandb.init(project="Data_Versioning"):
    
    # 1. Create an Artifact
    dataset_artifact = wandb.Artifact(
        name="raw_images", 
        type="dataset",
        description="The initial 10,000 images scraped from the web."
    )
    
    # 2. Add the folder of images
    dataset_artifact.add_dir("/local/path/to/images")
    
    # 3. Upload to the cloud!
    wandb.log_artifact(dataset_artifact)
```
*Effect:* Tomorrow, your teammate can run `run.use_artifact('raw_images:v1')` and WandB will instantly download the exact dataset you used, guaranteeing perfect reproducibility.

---

## 6. MAANG Interview Scenarios

### Scenario 1: PyTorch Lightning Integration
*Interviewer:* "I want to log my metrics to WandB, but I built my entire model using PyTorch Lightning (Guide 06). Where do I put the `wandb.log()` calls inside my `training_step`?"

*Answer:* "You don't! That is the beauty of modern frameworks. You should never manually write `wandb.log` inside a Lightning Module, because it tightly couples your model to a specific cloud vendor. Instead, we use Lightning's built-in `WandbLogger`. 
```python
from pytorch_lightning.loggers import WandbLogger
wandb_logger = WandbLogger(project='Lightning_Project')
trainer = pl.Trainer(logger=wandb_logger)
```
By simply passing the logger to the Trainer, every time you call `self.log('loss', loss)` inside your Lightning Module, it is automatically routed to the WandB cloud. If we ever switch back to TensorBoard, we just swap the Logger object, and we don't have to rewrite a single line of our neural network."

### Scenario 2: The GPU Temperature Crash
*Interviewer:* "We left a massive Llama-3 fine-tuning job running over the weekend. On Monday, the server had crashed. The Loss curve looked perfectly normal right up until the crash. How can WandB help us debug this?"

*Answer:* "WandB doesn't just log software metrics; it logs **System Metrics** automatically in the background. If we open the WandB dashboard and switch to the 'System' tab, we will see line charts for GPU Memory Utilization, GPU Temperature, and <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> usage. 
I would look at the GPU Temperature graph. If it spiked to 95°C right before the crash, we know it was a physical thermal throttling shutdown. If the System <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> graph slowly climbed from 10GB to 256GB and then flatlined, we know we have a Memory Leak in our Python `DataLoader` (likely holding onto tensors without calling `.detach()`), resulting in an <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>-level Out-Of-Memory kill."
