# 🧠 THE 180-DAY AI ENGINEERING MASTERPLAN
## From Absolute Zero to Principal <abbr title="Artificial Intelligence">AI</abbr> Engineer — 3 Hours/Day

> **Author's Note:** This is a production-grade, no-nonsense curriculum. Every day follows a strict 3-hour protocol. No hand-waving. No toy examples. You will build, break, and rebuild until the concepts are second nature. Every single day is fully specified — no skeletal placeholders, no gaps, no excuses.

---

## 📋 CURRICULUM METADATA

| Field | Value |
|---|---|
| **Duration** | 180 Days (6 Months) |
| **Daily Commitment** | 3 Hours (strict) |
| **Total Hours** | 540 Hours |
| **Prerequisites** | Basic Python, High-School Mathematics |
| **Target Level** | Principal <abbr title="Artificial Intelligence">AI</abbr> Engineer / MAANG Staff+ |
| **Stack** | Python, PyTorch, HuggingFace, LangChain, LangGraph, CrewAI, FastMCP, vLLM, Ray, Kubernetes, <abbr title="A set of platform as a service products that use OS-level virtualization to deliver software in packages called containers.">Docker</abbr>, MLflow |
| **Start Date** | ____/____/________ |
| **Target End Date** | ____/____/________ |

---

## 🗺️ PHASE ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       180-DAY CURRICULUM MAP                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 1 ▸ Days 001–030 ▸ Mathematical Foundations & Classical ML        │
│  PHASE 2 ▸ Days 031–060 ▸ Deep Learning & Neural Architectures          │
│  PHASE 3 ▸ Days 061–090 ▸ Transformers & Modern NLP                     │
│  PHASE 4 ▸ Days 091–120 ▸ LLMs: Training, Fine-Tuning & Alignment      │
│  PHASE 5 ▸ Days 121–150 ▸ Agentic AI, MCP & Tool-Use Systems           │
│  PHASE 6 ▸ Days 151–180 ▸ Production LLMOps & System Design             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Prerequisite Skill Check (Complete Before Day 1)

Before starting, ensure you can comfortably:

| Skill | Self-Assessment | Resources if Weak |
|---|---|---|
| Python basics (functions, classes, loops, list comprehensions) | ☐ Ready | Automate the Boring Stuff (free online) |
| Git & GitHub (clone, commit, push, branch, PR) | ☐ Ready | Pro Git Book (free online) |
| Terminal/Command Line (navigate, run scripts) | ☐ Ready | The Missing Semester (MIT, free) |
| High-school algebra & basic calculus (derivatives) | ☐ Ready | Khan Academy Calculus (free) |
| Basic statistics (mean, median, standard deviation) | ☐ Ready | Khan Academy Statistics (free) |

### 🚨 Parallel Track: The Google <abbr title="Artificial Intelligence">AI</abbr> Engineer Requirement (DSA & LeetCode)
If your ultimate goal is a **Google <abbr title="Artificial Intelligence">AI</abbr> Engineer** position, you CANNOT escape traditional Data Structures & Algorithms. Google conducts 2-3 standard coding interviews (medium/hard) for almost all <abbr title="Machine Learning">ML</abbr>/<abbr title="Artificial Intelligence">AI</abbr> roles.
- **Requirement:** You must solve 1-2 LeetCode problems daily alongside this 180-day plan.
- **Focus Areas:** Graphs (<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>), Dynamic Programming, Trees, Sliding Window, Two Pointers.
- **Goal:** Consistently solve Mediums in 20 minutes and Hards in 40 minutes.

---

## ⏱️ DAILY 3-HOUR SESSION FORMAT

Every single day follows this exact protocol:

| Segment | Duration | Focus | Deliverable |
|---|---|---|---|
| **HOUR 1** | 60 min | Deep Theory & Mathematics | Handwritten/typed notes with LaTeX derivations |
| **HOUR 2** | 60 min | Guided Code-Along | Production-grade Python script, committed to repo |
| **HOUR 3** | 60 min | Solo Build + MAANG Prep | Blank-slate challenge + interview answer draft |

### Daily Checklist Template

```markdown
## Day [XXX] — [Topic Name]
**Date:** ____/____/________
**Phase:** [1-6] | **Week:** [1-26]

### Pre-Session
- [ ] Reviewed yesterday's notes (10 min)
- [ ] Environment ready, GPU available if needed

### Hour 1: Theory (60 min)
- [ ] Read/watched prerequisite material
- [ ] Completed mathematical derivations
- [ ] Wrote summary notes with key formulas
- [ ] Drew architecture diagram (if applicable)

### Hour 2: Code-Along (60 min)
- [ ] Typed (not copied) all code
- [ ] Code runs without errors
- [ ] Added type hints and docstrings
- [ ] Committed to repo with descriptive message
- [ ] Wrote at least 2 unit tests

### Hour 3: Challenge + Interview (60 min)
- [ ] Completed solo challenge WITHOUT looking at Hour 2 code
- [ ] Wrote interview answer (minimum 300 words)
- [ ] Identified 2-3 concepts still unclear → added to review list

### Post-Session Reflection
- **Confidence Level:** [1-5] ⭐
- **Hardest Concept:**
- **Key Insight:**
- **Tomorrow's Prep:**
```

---

# ═══════════════════════════════════════════════════════════════
# PHASE 1: MATHEMATICAL FOUNDATIONS & CLASSICAL ML
# Days 001–030 | "Build the Bedrock"
# ═══════════════════════════════════════════════════════════════

> **Phase Objective:** Internalize the mathematical machinery that powers every <abbr title="Machine Learning">ML</abbr> algorithm. You cannot shortcut this. Every gradient, every matrix decomposition, every probability distribution you master here pays compound interest in Phases 3–6.

### Phase 1 Milestone Checklist
- [ ] Can derive gradient descent update rules from scratch
- [ ] Can implement PCA, SVD, KNN, Linear/Logistic Regression without any library
- [ ] Can explain Bayes' theorem with a real-world example and do the math
- [ ] Can implement and compare 5+ ML algorithms on a tabular dataset
- [ ] Can articulate bias-variance trade-off with mathematical precision
- [ ] Can design an end-to-end ML pipeline on a whiteboard

---

## Week 1: Linear Algebra for ML (Days 1–7)

### Day 001 — Vectors, Dot Products & Geometric Intuition
- **Hour 1 Theory:** Vectors as ordered lists vs. geometric arrows. Dot product formula: $\mathbf{a} \cdot \mathbf{b} = \sum_{i=1}^{n} a_i b_i = \|\mathbf{a}\| \|\mathbf{b}\| \cos\theta$. Geometric interpretation: projection, similarity. Why cosine similarity is the backbone of embedding search. Orthogonality and its meaning in feature spaces.
- **Hour 2 Code:** NumPy implementation of vector operations. Build a cosine similarity function from scratch. Benchmark against `scipy.spatial.distance.cosine`. Implement orthogonal projection.
- **Hour 3 Challenge:** Implement a document similarity engine using TF-IDF vectors and cosine similarity (no libraries for the similarity computation). **Interview Q:** "How does cosine similarity differ from Euclidean distance for high-dimensional sparse data, and when would you choose one over the other in a production recommendation system?"

### Day 002 — Matrix Operations & Transformations
- **Hour 1 Theory:** Matrix as a linear transformation. Matrix multiplication as composition of transformations: $(AB)\mathbf{x} = A(B\mathbf{x})$. Transpose, trace, determinant. Why matrix multiplication is $O(n^3)$ and Strassen's $O(n^{2.807})$. Rank, nullity, and the rank-nullity theorem.
- **Hour 2 Code:** Implement matrix multiplication from scratch (triple nested loop), then with NumPy broadcasting. Visualize 2D linear transformations (rotation, scaling, shearing) with matplotlib.
- **Hour 3 Challenge:** Build a 2D image transformation pipeline (rotate, scale, translate) using only matrix operations. **Interview Q:** "You're designing a feature store that needs to perform millions of matrix-vector multiplications per second. Walk me through the hardware and software optimization stack."

### Day 003 — Eigenvalues, Eigenvectors & Spectral Decomposition
- **Hour 1 Theory:** Eigenvalue equation $A\mathbf{v} = \lambda\mathbf{v}$. Characteristic polynomial $\det(A - \lambda I) = 0$. Spectral theorem for symmetric matrices. Why eigenvectors are the "natural coordinates" of a transformation. Positive definite matrices and their role in optimization.
- **Hour 2 Code:** Implement power iteration for dominant eigenvector. Compare with `numpy.linalg.eig`. Visualize eigenvectors of a covariance matrix.
- **Hour 3 Challenge:** Implement PCA from scratch using eigendecomposition on the MNIST dataset. **Interview Q:** "Explain how Google's PageRank algorithm fundamentally relies on eigenvector computation. How would you scale this to billions of web pages?"

### Day 004 — Singular Value Decomposition (SVD)
- **Hour 1 Theory:** Full derivation: $A = U\Sigma V^T$. Relationship to eigendecomposition: $A^TA = V\Sigma^2 V^T$. Truncated SVD for dimensionality reduction. Eckart-Young theorem: best rank-$k$ approximation minimizes Frobenius norm. Connection to matrix completion and recommendation systems.
- **Hour 2 Code:** Implement truncated SVD from scratch. Apply to image compression (show reconstruction at various ranks). Compare with `sklearn.decomposition.TruncatedSVD`.
- **Hour 3 Challenge:** Build a basic collaborative filtering recommender using SVD on the MovieLens-100k dataset. **Interview Q:** "How does SVD underpin latent semantic analysis in NLP, and what are its failure modes at scale?"

### Day 005 — Norms, Distances & Metric Spaces
- **Hour 1 Theory:** $L_1$ (Manhattan), $L_2$ (Euclidean), $L_\infty$ (Chebyshev) norms. Generalized $L_p$ norm: $\|\mathbf{x}\|_p = \left(\sum_i |x_i|^p\right)^{1/p}$. Frobenius norm for matrices. Why $L_1$ promotes sparsity (connection to Lasso). Mahalanobis distance. Metric space axioms: non-negativity, identity, symmetry, triangle inequality.
- **Hour 2 Code:** Implement all norm functions. Visualize unit balls for $L_1, L_2, L_\infty$ in 2D. Show sparsity-inducing property of $L_1$ with synthetic regression.
- **Hour 3 Challenge:** Build a KNN classifier from scratch using configurable distance metrics. Test on Iris dataset. **Interview Q:** "In a production anomaly detection system, why might Mahalanobis distance outperform Euclidean distance? What are the computational trade-offs?"

### Day 006 — Matrix Calculus & Jacobians
- **Hour 1 Theory:** Gradient of scalar function: $\nabla f = \left[\frac{\partial f}{\partial x_1}, \ldots, \frac{\partial f}{\partial x_n}\right]^T$. Jacobian matrix for vector-valued functions. Hessian matrix for second-order information. Chain rule in matrix form. Why this is the mathematical engine behind backpropagation.
- **Hour 2 Code:** Implement numerical gradient checking. Compute Jacobians for simple neural network layers. Verify against PyTorch autograd.
- **Hour 3 Challenge:** Derive and implement the gradient of softmax cross-entropy loss by hand, then verify numerically. **Interview Q:** "Walk me through the full backpropagation derivation for a 2-layer MLP with ReLU activations. Where do numerical instabilities arise?"

### Day 007 — Review & Integration Lab
- **Hour 1 Theory:** Comprehensive review. Connect all concepts: vectors → matrices → eigendecomposition → SVD → norms → calculus. Draw the complete dependency graph. Identify which concepts map to which ML algorithms.
- **Hour 2 Code:** Build a complete "ML Math Toolkit" library with all implementations from the week. Add unit tests with pytest. Create a proper Python package structure with `__init__.py`.
- **Hour 3 Challenge:** Implement a full PCA pipeline from raw data to visualization, using ONLY your toolkit (no sklearn). **Interview Q:** "Design a linear algebra computation service that can handle 10,000 concurrent requests for matrix operations on matrices up to 10,000 × 10,000. Discuss memory, compute, and latency trade-offs."

---

## Week 2: Probability, Statistics & Information Theory (Days 8–14)

### Day 008 — Probability Axioms, Bayes' Theorem & Conditional Probability
- **Hour 1 Theory:** Kolmogorov axioms. Joint, marginal, conditional probability. Bayes' theorem: $P(A|B) = \frac{P(B|A)P(A)}{P(B)}$. Prior, likelihood, posterior, evidence. Conjugate priors. Independence vs conditional independence.
- **Hour 2 Code:** Implement a Naive Bayes spam classifier from scratch. Compute posteriors with Laplace smoothing.
- **Hour 3 Challenge:** Build a medical diagnostic classifier using Bayes' theorem (disease prevalence as prior). **Interview Q:** "A production fraud detection system has 0.1% fraud rate. Your model has 99% recall and 95% precision. What's the actual probability a flagged transaction is fraudulent? How do you communicate this to stakeholders?"

### Day 009 — Probability Distributions Deep Dive
- **Hour 1 Theory:** Bernoulli, Binomial, Poisson, Gaussian, Exponential, Beta, Dirichlet. PDF/PMF/CDF derivations. Moment generating functions. Central Limit Theorem proof sketch. Multivariate Gaussian: $p(x) = \frac{1}{(2\pi)^{d/2}|\Sigma|^{1/2}}\exp\left(-\frac{1}{2}(x-\mu)^T\Sigma^{-1}(x-\mu)\right)$.
- **Hour 2 Code:** Implement PDF/PMF for each distribution from scratch. Visualize CLT with increasing sample sizes. Monte Carlo estimation of $\pi$ using uniform distribution.
- **Hour 3 Challenge:** Build a distribution fitter that takes data and identifies the best-fit distribution using MLE. **Interview Q:** "Your A/B testing platform serves 100M users. Explain why the Gaussian approximation works, when it breaks, and what you'd use instead."

### Day 010 — Maximum Likelihood Estimation (MLE) & MAP
- **Hour 1 Theory:** Likelihood function $\mathcal{L}(\theta|X) = \prod_{i=1}^n p(x_i|\theta)$. Log-likelihood trick. MLE derivation for Gaussian parameters. MAP: $\hat{\theta}_{MAP} = \arg\max_\theta p(\theta|X) = \arg\max_\theta p(X|\theta)p(\theta)$. Connection: MAP with flat prior = MLE. MAP with Gaussian prior = $L_2$ regularization. Expectation-Maximization (EM) algorithm overview.
- **Hour 2 Code:** Implement MLE for Gaussian, Bernoulli, and Poisson from scratch. Implement MAP with Gaussian prior. Visualize how prior strength affects posterior.
- **Hour 3 Challenge:** Build a Bayesian linear regression from scratch with configurable prior strength. **Interview Q:** "Explain the exact mathematical relationship between MAP estimation, $L_2$ regularization, and Ridge regression. When would you prefer a fully Bayesian approach in production?"

### Day 011 — Information Theory: Entropy, Cross-Entropy & KL Divergence
- **Hour 1 Theory:** Shannon entropy: $H(X) = -\sum_x p(x)\log p(x)$. Cross-entropy: $H(p,q) = -\sum_x p(x)\log q(x)$. KL divergence: $D_{KL}(p\|q) = \sum_x p(x)\log\frac{p(x)}{q(x)}$. Relationship: $H(p,q) = H(p) + D_{KL}(p\|q)$. Why cross-entropy is the standard classification loss. Mutual information: $I(X;Y) = H(X) - H(X|Y)$.
- **Hour 2 Code:** Implement entropy, cross-entropy, KL divergence. Visualize KL divergence between two Gaussians as parameters change. Show asymmetry of KL.
- **Hour 3 Challenge:** Build a decision tree that uses information gain (entropy reduction) for splitting. **Interview Q:** "In RLHF for LLMs, we use KL divergence as a penalty between the policy model and reference model. Derive why, and explain what happens when the KL penalty coefficient is too high or too low."

### Day 012 — Sampling Methods: MCMC, Gibbs, Metropolis-Hastings
- **Hour 1 Theory:** Monte Carlo integration. Markov Chain convergence. Metropolis-Hastings algorithm derivation. Detailed balance condition. Gibbs sampling as special case. Importance sampling. Why sampling matters for Bayesian inference at scale.
- **Hour 2 Code:** Implement Metropolis-Hastings sampler for a 2D Gaussian mixture. Visualize chain convergence. Implement Gibbs sampler for a bivariate Gaussian. Implement importance sampling.
- **Hour 3 Challenge:** Use MCMC to perform Bayesian inference on a logistic regression model. **Interview Q:** "You need to serve Bayesian model predictions with <10ms latency. MCMC is too slow. What alternatives exist, and what are their trade-offs?"

### Day 013 — Hypothesis Testing, Confidence Intervals & A/B Testing
- **Hour 1 Theory:** Null/alternative hypotheses. p-values (what they actually mean). Type I/II errors. Power analysis. Confidence intervals via CLT. Bootstrap methods. Multiple comparison correction (Bonferroni, FDR). Bayesian A/B testing.
- **Hour 2 Code:** Implement t-test, chi-squared test, and bootstrap confidence intervals from scratch. Build an A/B testing simulator with power analysis.
- **Hour 3 Challenge:** Design and implement a sequential A/B testing framework that controls false positive rate. **Interview Q:** "Your team runs 200 A/B tests per quarter. The PM says a test with p=0.04 is 'significant.' What's wrong, and how do you redesign the experimentation platform?"

### Day 014 — Week 2 Review & Probabilistic Programming
- **Hour 1 Theory:** Unify all concepts into a probabilistic graphical model framework. Directed vs undirected models. Factor graphs. Variable elimination. Belief propagation overview.
- **Hour 2 Code:** Build a simple probabilistic programming mini-framework that supports variable declaration, conditioning, and inference via rejection sampling.
- **Hour 3 Challenge:** Model a real-world problem (e.g., student grade prediction) as a Bayesian network and perform inference. **Interview Q:** "Design a real-time Bayesian personalization engine for a streaming platform with 50M users. How do you handle cold start, scalability, and model updates?"

---

## Week 3: Optimization Theory (Days 15–21)

### Day 015 — Gradient Descent from First Principles
- **Hour 1 Theory:** Convex vs non-convex functions. Gradient descent update rule: $\theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L}(\theta_t)$. Convergence conditions. Learning rate analysis. Lipschitz continuity and convergence rate $O(1/T)$. Convexity guarantees global minimum.
- **Hour 2 Code:** Implement GD for linear regression. Visualize loss surface and gradient trajectory in 3D. Implement learning rate schedules (step, exponential, cosine annealing).
- **Hour 3 Challenge:** Implement GD on Rosenbrock function and visualize convergence with different learning rates. **Interview Q:** "Why is the choice of learning rate the single most important hyperparameter in deep learning? Discuss the relationship between learning rate, batch size, and generalization."

### Day 016 — SGD, Mini-Batch SGD & Variance Reduction
- **Hour 1 Theory:** Stochastic gradient as unbiased estimator: $\mathbb{E}[\nabla_\theta \mathcal{L}_i] = \nabla_\theta \mathcal{L}$. Variance of stochastic gradient. Mini-batch variance reduction: $\text{Var} \propto 1/B$. Linear scaling rule for learning rate. Gradient noise as implicit regularization.
- **Hour 2 Code:** Implement SGD, mini-batch SGD with configurable batch size. Compare convergence curves. Implement gradient accumulation for effective large batches.
- **Hour 3 Challenge:** Train a logistic regression on MNIST using your SGD implementation. Experiment with batch sizes. **Interview Q:** "Google trains models with batch sizes of 32,768. Explain the linear scaling rule, warmup, and LARS/LAMB optimizers. What breaks at extreme batch sizes?"

### Day 017 — Momentum, Nesterov, RMSProp & Adam
- **Hour 1 Theory:** Momentum: $v_t = \beta v_{t-1} + \nabla_\theta \mathcal{L}$, $\theta_{t+1} = \theta_t - \eta v_t$. Nesterov lookahead. RMSProp adaptive learning rates. Adam: $m_t = \beta_1 m_{t-1} + (1-\beta_1)g_t$, $v_t = \beta_2 v_{t-1} + (1-\beta_2)g_t^2$, bias correction $\hat{m}_t = m_t/(1-\beta_1^t)$. AdamW weight decay fix.
- **Hour 2 Code:** Implement Momentum, RMSProp, Adam, AdamW optimizers from scratch. Compare convergence on a non-convex loss surface. Visualize adaptive learning rates.
- **Hour 3 Challenge:** Build a modular Optimizer base class with all variants. Benchmark on a 3-layer MLP. **Interview Q:** "Adam is the default optimizer, but many state-of-the-art results use SGD with momentum. When and why would you switch? Discuss the generalization gap."

### Day 018 — Learning Rate Scheduling & Warmup Strategies
- **Hour 1 Theory:** Step decay, exponential decay, cosine annealing: $\eta_t = \eta_{min} + \frac{1}{2}(\eta_{max} - \eta_{min})(1 + \cos(\pi t/T))$. Cyclical learning rates. 1cycle policy. Warmup rationale: why transformers need warmup (gradient scale instability in early training). Cosine annealing with warm restarts.
- **Hour 2 Code:** Implement all schedulers. Visualize LR curves. Train a model with 1cycle policy and compare with constant LR.
- **Hour 3 Challenge:** Implement a learning rate finder (sweep LR from 1e-7 to 10, plot loss vs LR). **Interview Q:** "You're training a 7B parameter LLM. Design the complete learning rate schedule including warmup, peak, decay, and cooldown phases. Justify each choice."

### Day 019 — Regularization: L1, L2, Dropout, Early Stopping
- **Hour 1 Theory:** $L_2$ regularization: $\mathcal{L}_{reg} = \mathcal{L} + \frac{\lambda}{2}\|\theta\|_2^2$. Bayesian interpretation (Gaussian prior). $L_1$ and sparsity (Laplace prior). Dropout as approximate Bayesian inference. Early stopping as implicit regularization. Bias-variance decomposition: $\text{Error} = \text{Bias}^2 + \text{Variance} + \text{Noise}$. Data augmentation as regularization.
- **Hour 2 Code:** Implement L1, L2 regularization from scratch. Implement dropout (training mask, inference scaling). Visualize bias-variance trade-off with polynomial regression.
- **Hour 3 Challenge:** Train an overfit model on a small dataset, then systematically apply each regularization technique and measure effect. **Interview Q:** "You're seeing a 15% gap between training and validation accuracy on a production model. Walk through your systematic debugging process."

### Day 020 — Convex Optimization & Constrained Optimization
- **Hour 1 Theory:** Convex sets and functions. KKT conditions. Lagrange multipliers. Duality. Support Vector Machine as constrained optimization: $\min \frac{1}{2}\|\mathbf{w}\|^2$ s.t. $y_i(\mathbf{w}\cdot\mathbf{x}_i + b) \geq 1$. Dual formulation and kernel trick.
- **Hour 2 Code:** Implement SVM using quadratic programming (cvxopt). Implement kernel SVM with RBF kernel. Visualize decision boundaries.
- **Hour 3 Challenge:** Build a soft-margin SVM from scratch with SMO algorithm. **Interview Q:** "SVMs were dominant before deep learning. What mathematical properties made them theoretically attractive? Why did deep learning win, and where do SVMs still outperform?"

### Day 021 — Week 3 Review & Optimization in Practice
- **Hour 1 Theory:** Unify: loss landscapes of deep networks, saddle points vs. local minima (Dauphin et al.), sharp vs. flat minima and generalization (SAM optimizer). Gradient clipping, mixed precision training. Second-order methods: Newton's method, L-BFGS and why they don't scale.
- **Hour 2 Code:** Implement gradient clipping, gradient scaling for mixed precision. Build a training loop with all best practices combined.
- **Hour 3 Challenge:** Train a model using your complete optimizer toolkit and achieve best validation accuracy. **Interview Q:** "You're the tech lead for a training infrastructure team. A researcher reports that training loss plateaus at epoch 50/100. Describe your diagnostic playbook."

---

## Week 4: Classical ML Algorithms & Data Engineering (Days 22–30)

### Day 022 — Linear Regression: OLS, Ridge, Lasso, ElasticNet
- **Hour 1 Theory:** Normal equation: $\hat{\theta} = (X^TX)^{-1}X^Ty$. Ridge: $(X^TX + \lambda I)^{-1}X^Ty$. Lasso via coordinate descent. ElasticNet. Multicollinearity and condition number. Heteroscedasticity and weighted least squares.
- **Hour 2 Code:** Implement all variants from scratch. Compare with sklearn. Feature importance via coefficient analysis.
- **Hour 3 Challenge:** Build a housing price predictor with feature engineering pipeline. **Interview Q:** "Your linear regression has a condition number of $10^{15}$. Diagnose and fix."

### Day 023 — Logistic Regression & Softmax Regression
- **Hour 1 Theory:** Sigmoid: $\sigma(z) = 1/(1+e^{-z})$. Log-loss derivation from MLE. Newton's method for logistic regression. Multinomial extension with softmax. Numerical stability of log-sum-exp trick. Logistic regression as a single-layer neural network.
- **Hour 2 Code:** Implement binary and multinomial logistic regression from scratch with gradient descent and Newton's method.
- **Hour 3 Challenge:** Build a multi-class text classifier using logistic regression on TF-IDF features. **Interview Q:** "Explain the log-sum-exp trick and why it's critical in production softmax implementations."

### Day 024 — Decision Trees & Information-Theoretic Splitting
- **Hour 1 Theory:** ID3, C4.5, CART algorithms. Gini impurity: $G = 1 - \sum p_i^2$. Information gain. Gain ratio. Pruning: pre-pruning (max depth, min samples) vs. post-pruning (cost-complexity). Decision trees for regression (variance reduction splitting).
- **Hour 2 Code:** Implement CART decision tree from scratch with both Gini and entropy criteria. Visualize the tree.
- **Hour 3 Challenge:** Implement cost-complexity pruning and find optimal alpha via cross-validation. **Interview Q:** "Why are decision trees high-variance models? How does this property make them ideal base learners for ensembles?"

### Day 025 — Ensemble Methods: Bagging, Random Forests
- **Hour 1 Theory:** Bootstrap aggregating. Variance reduction: $\text{Var}(\bar{X}) = \frac{\sigma^2}{n}(1 + (n-1)\rho)$. Random feature subsampling reduces $\rho$. Out-of-bag error estimation. Feature importance via permutation and impurity decrease. Extremely Randomized Trees (ExtraTrees).
- **Hour 2 Code:** Implement Random Forest from scratch using your Day 24 decision tree. Implement OOB error and feature importance.
- **Hour 3 Challenge:** Build a Random Forest that beats sklearn's on a tabular dataset by tuning the right hyperparameters. **Interview Q:** "When would you choose Random Forest over XGBoost for a production tabular ML system? Discuss latency, interpretability, and maintenance."

### Day 026 — Boosting: AdaBoost, Gradient Boosting, XGBoost, LightGBM
- **Hour 1 Theory:** AdaBoost: sequential weak learner weighting $\alpha_t = \frac{1}{2}\ln\frac{1-\epsilon_t}{\epsilon_t}$. Gradient Boosting: functional gradient descent in function space. XGBoost: regularized objective $\mathcal{L} = \sum l(y_i, \hat{y}_i) + \sum \Omega(f_k)$, second-order Taylor expansion, optimal leaf weights. LightGBM: histogram-based splitting, GOSS, EFB. CatBoost: ordered boosting for categorical features.
- **Hour 2 Code:** Implement AdaBoost and Gradient Boosting from scratch. Compare with XGBoost, LightGBM, CatBoost libraries on Kaggle dataset.
- **Hour 3 Challenge:** Implement a gradient boosting machine with custom loss function support. **Interview Q:** "You're designing a real-time bidding system. The model must predict click probability for 1M auctions/second. Compare XGBoost vs. neural approaches for this use case."

### Day 027 — Unsupervised Learning: K-Means, GMMs, DBSCAN
- **Hour 1 Theory:** K-Means as EM for isotropic Gaussians. Lloyd's algorithm convergence. K-Means++ initialization. GMMs: full EM derivation with E-step and M-step. DBSCAN: density-based with $\epsilon$-neighborhoods. HDBSCAN for varying density. Silhouette score, Davies-Bouldin index.
- **Hour 2 Code:** Implement K-Means++, GMM with EM, and DBSCAN from scratch. Compare clustering quality with silhouette scores.
- **Hour 3 Challenge:** Build a customer segmentation pipeline with automatic cluster selection (elbow + silhouette). **Interview Q:** "Design a real-time user clustering system for 100M users. How do you handle cluster drift, new users, and scalability?"

### Day 028 — Dimensionality Reduction: PCA, t-SNE, UMAP
- **Hour 1 Theory:** PCA: maximize variance = minimize reconstruction error. Kernel PCA for non-linear reduction. t-SNE: Student-t kernel in low-dimensional space, KL divergence minimization, perplexity. UMAP: fuzzy simplicial sets, cross-entropy optimization. Why t-SNE distances are meaningless. When to use each method.
- **Hour 2 Code:** Implement PCA from scratch, use sklearn for t-SNE/UMAP. Visualize MNIST in 2D with all three methods. Compare computation times.
- **Hour 3 Challenge:** Build an interactive embedding visualizer for a dataset of your choice. **Interview Q:** "Your team uses t-SNE to 'prove' clusters exist. Why is this dangerous, and what additional evidence would you require?"

### Day 029 — Model Evaluation, Hyperparameter Tuning & Explainability
- **Hour 1 Theory:** Precision, Recall, F1, AUC-ROC, AUC-PR. When to use what (class imbalance → PR curve). K-fold, stratified K-fold, time-series split. Calibration: Platt scaling, isotonic regression. Brier score. Hyperparameter tuning: grid search, random search, Bayesian optimization (Gaussian processes for hyperparameter search), Optuna. SHAP values: $\phi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N|-|S|-1)!}{|N|!}[f(S \cup \{i\}) - f(S)]$. LIME: local linear approximations. Partial dependence plots.
- **Hour 2 Code:** Implement all metrics from scratch. Build a cross-validation framework. Implement Platt scaling for calibration. Use Optuna for hyperparameter tuning. Compute SHAP values using the shap library.
- **Hour 3 Challenge:** Build a complete model evaluation report generator with visualizations, SHAP explanations, and hyperparameter tuning. **Interview Q:** "Your binary classifier has AUC-ROC of 0.95 but AUC-PR of 0.12. Explain what's happening and how you'd communicate this to the VP of Product."

### Day 030 — Phase 1 Capstone: End-to-End ML Pipeline
- **Hour 1 Theory:** ML system design: data ingestion → feature engineering → model training → evaluation → deployment → monitoring. Feature stores, model registries, experiment tracking. Data versioning with DVC. Reproducibility: random seeds, deterministic training, environment locking.
- **Hour 2 Code:** Build a complete ML pipeline for a tabular prediction task using only your implementations from Phase 1. Add logging, config management (Hydra/YAML), experiment tracking (MLflow), and reproducibility.
- **Hour 3 Challenge:** Rebuild the entire pipeline from memory. **Interview Q:** "Design a fraud detection system that processes 50,000 transactions per second with <50ms latency. Cover data pipeline, feature engineering, model serving, and monitoring. Discuss cold start and concept drift."

---

# ═══════════════════════════════════════════════════════════════
# PHASE 2: DEEP LEARNING & NEURAL ARCHITECTURES
# Days 031–060 | "Enter the Neural Network"
# ═══════════════════════════════════════════════════════════════

> **Phase Objective:** Master neural networks from single neurons to complex architectures. By Day 60, you should be able to implement any standard architecture in raw PyTorch and understand every line.

### Phase 2 Milestone Checklist
- [ ] Can implement backpropagation from scratch with computational graphs
- [ ] Can build CNN, RNN, LSTM, GRU from raw PyTorch (no nn.LSTM etc.)
- [ ] Can train a ResNet on CIFAR-10 achieving >90% accuracy
- [ ] Can implement a VAE and generate new samples
- [ ] Can explain vanishing gradients mathematically and propose solutions
- [ ] Can build a seq2seq model with attention for translation

---

## Week 5: Neural Network Fundamentals (Days 31–37)

### Day 031 — The Perceptron & Universal Approximation Theorem
- **Hour 1 Theory:** McCulloch-Pitts neuron. Perceptron learning rule and convergence theorem. XOR problem and its significance. Universal Approximation Theorem (Cybenko, 1989): a single hidden layer with sufficient neurons can approximate any continuous function on a compact set. Why depth > width in practice. Representation vs optimization.
- **Hour 2 Code:** Implement Perceptron from scratch. Demonstrate XOR failure. Implement a 2-layer MLP that solves XOR. Visualize decision boundaries evolving during training.
- **Hour 3 Challenge:** Implement a multi-layer perceptron from scratch (no PyTorch) for MNIST. **Interview Q:** "The Universal Approximation Theorem guarantees a solution exists. Why doesn't this guarantee that gradient descent will find it?"

### Day 032 — Activation Functions: ReLU, GELU, SiLU, Swish
- **Hour 1 Theory:** Sigmoid saturation and vanishing gradients. ReLU: $f(x) = \max(0,x)$ and dying ReLU problem. Leaky ReLU, PReLU, ELU. GELU: $f(x) = x \cdot \Phi(x)$ (used in BERT/GPT). SiLU/Swish: $f(x) = x \cdot \sigma(x)$ (used in LLaMA). Why smooth activations matter for optimization. Mish activation.
- **Hour 2 Code:** Implement all activation functions and their derivatives. Visualize forward and backward passes. Compare gradient flow through deep networks with different activations.
- **Hour 3 Challenge:** Train identical architectures with each activation function on CIFAR-10 and compare. **Interview Q:** "LLaMA uses SiLU while BERT uses GELU. Explain the mathematical properties that drive these choices and what happens if you swap them."

### Day 033 — Backpropagation: Full Derivation & Computational Graphs
- **Hour 1 Theory:** Chain rule over computational graphs. Forward pass: compute values. Backward pass: compute gradients. Derive backprop for a 3-layer MLP with softmax-cross-entropy loss — every single partial derivative. Automatic differentiation: forward mode vs reverse mode. Jacobian-vector products (JVP) and vector-Jacobian products (VJP).
- **Hour 2 Code:** Implement a minimal autograd engine (inspired by Andrej Karpathy's micrograd). Support: add, multiply, power, ReLU, backward().
- **Hour 3 Challenge:** Extend your autograd engine to support matrix operations and train a small MLP. **Interview Q:** "PyTorch's autograd uses reverse-mode AD. When would forward-mode AD be more efficient? Discuss the Jacobian shape argument."

### Day 034 — Weight Initialization: Xavier, Kaiming, Orthogonal
- **Hour 1 Theory:** Random init and signal propagation. Xavier/Glorot: $\text{Var}(W) = 2/(n_{in} + n_{out})$ — derived from preserving variance through linear layers. Kaiming/He: $\text{Var}(W) = 2/n_{in}$ — corrected for ReLU. Orthogonal initialization. Fixup initialization for residual networks. Data-dependent initialization (LSUV).
- **Hour 2 Code:** Implement each initialization scheme. Measure activation statistics (mean, variance) through 50-layer networks with each init. Visualize "activation collapse" with bad init.
- **Hour 3 Challenge:** Build an initialization diagnostic tool that recommends the best init scheme given an architecture. **Interview Q:** "You're training a 100-layer network and observing NaN losses after 10 steps. Walk through your diagnostic process, starting from initialization."

### Day 035 — Loss Functions: Cross-Entropy, Focal, Contrastive, Triplet
- **Hour 1 Theory:** Cross-entropy derivation from MLE. Binary vs categorical. Focal loss: $FL(p_t) = -\alpha_t(1-p_t)^\gamma \log(p_t)$ — why it helps with class imbalance. Contrastive loss, triplet loss with margin. InfoNCE loss (used in CLIP, SimCLR). Label smoothing: soft targets $y_{smooth} = (1-\epsilon)y + \epsilon/K$.
- **Hour 2 Code:** Implement all loss functions in PyTorch. Train a model with focal loss on imbalanced dataset. Implement hard negative mining for triplet loss.
- **Hour 3 Challenge:** Build a face verification system using triplet loss on a face dataset. **Interview Q:** "CLIP uses InfoNCE loss to align vision and language. Derive the loss function and explain how the batch size affects the quality of negative samples."

### Day 036 — Batch Normalization, Layer Normalization & RMSNorm
- **Hour 1 Theory:** Internal covariate shift hypothesis (and its critique). BatchNorm: $\hat{x} = \frac{x - \mu_B}{\sqrt{\sigma_B^2 + \epsilon}}$, learnable $\gamma, \beta$. Running statistics at inference. LayerNorm: normalize over features (used in Transformers). RMSNorm: $\hat{x} = \frac{x}{\text{RMS}(x)} \cdot \gamma$ where $\text{RMS}(x) = \sqrt{\frac{1}{n}\sum x_i^2}$ (used in LLaMA). GroupNorm, InstanceNorm. When to use each.
- **Hour 2 Code:** Implement BatchNorm, LayerNorm, RMSNorm from scratch in PyTorch (custom nn.Module). Verify outputs match PyTorch built-ins. Measure training speed difference.
- **Hour 3 Challenge:** Train the same model with BN, LN, RMSNorm and compare convergence + final accuracy. **Interview Q:** "Why do Transformers use LayerNorm instead of BatchNorm? What goes wrong with BatchNorm in sequence models? Why is LLaMA's choice of RMSNorm significant?"

### Day 037 — PyTorch Deep Dive: Modules, Datasets, DataLoaders
- **Hour 1 Theory:** PyTorch execution model: eager vs graph mode. `nn.Module` lifecycle: `__init__`, `forward`, `parameters()`, `state_dict()`. Custom `Dataset` and `DataLoader` with multiprocessing. Memory pinning, prefetching. `torch.compile` and TorchScript. Profiling with `torch.profiler`.
- **Hour 2 Code:** Build a production-grade training framework: custom Dataset, DataLoader with augmentations, model, training loop with gradient accumulation, checkpointing, and logging (TensorBoard/WandB).
- **Hour 3 Challenge:** Refactor into a configurable training framework that takes a YAML config file. **Interview Q:** "Your DataLoader is the bottleneck in training. GPU utilization is 40%. Diagnose and fix."

---

## Week 6: Convolutional Neural Networks (Days 38–42)

### Day 038 — Convolution Operation: Math & Intuition
- **Hour 1 Theory:** 1D and 2D convolution: $(f * g)(t) = \sum_\tau f(\tau)g(t-\tau)$. Cross-correlation (what frameworks actually implement). Stride, padding (same/valid), dilation (atrous convolution). Output size formula: $O = \lfloor(I - K + 2P)/S\rfloor + 1$. Parameter sharing and translation equivariance. Transposed convolution for upsampling.
- **Hour 2 Code:** Implement 2D convolution from scratch (naive loops, then im2col). Verify against `F.conv2d`. Visualize learned filters.
- **Hour 3 Challenge:** Implement a conv layer that supports stride, padding, and dilation from scratch. **Interview Q:** "Explain the im2col trick and why it converts convolution to matrix multiplication. What are the memory implications?"

### Day 039 — CNN Architectures: LeNet → AlexNet → VGG → ResNet
- **Hour 1 Theory:** LeNet-5 architecture. AlexNet innovations (ReLU, dropout, GPU training). VGG: "deeper is better" with 3×3 filters (two 3×3 = one 5×5 receptive field with fewer params). ResNet: skip connections solve vanishing gradients. Mathematical analysis: $\frac{\partial \mathcal{L}}{\partial x_l} = \frac{\partial \mathcal{L}}{\partial x_L} \prod_{i=l}^{L-1}(1 + \frac{\partial F_i}{\partial x_i})$. DenseNet: feature reuse.
- **Hour 2 Code:** Implement ResNet-18 from scratch in PyTorch. Train on CIFAR-10. Implement residual blocks with proper BatchNorm placement (pre-activation vs post-activation).
- **Hour 3 Challenge:** Implement ResNet-50 with bottleneck blocks from scratch. **Interview Q:** "You need to deploy an image classification model on a mobile device with 2GB RAM. Walk through model architecture selection, quantization, and optimization."

### Day 040 — Modern CNNs: EfficientNet, ConvNeXt & MobileNet
- **Hour 1 Theory:** Depthwise separable convolutions (MobileNet): parameter reduction from $K^2 \cdot C_{in} \cdot C_{out}$ to $K^2 \cdot C_{in} + C_{in} \cdot C_{out}$. EfficientNet compound scaling (width, depth, resolution). ConvNeXt: "modernizing" CNNs with Transformer tricks (larger kernels, fewer activations, LayerNorm). Inverted residual bottleneck (MobileNet-v2). Neural Architecture Search (NAS) overview.
- **Hour 2 Code:** Implement depthwise separable conv block, MobileNet-v2 inverted residual block. Compare FLOPs and parameters.
- **Hour 3 Challenge:** Build a custom efficient architecture for a specific FLOPs budget. **Interview Q:** "EfficientNet vs ConvNeXt vs Vision Transformer for production image classification. Discuss accuracy, latency, and scaling behavior."

### Day 041 — Object Detection: YOLO Architecture & Multi-Scale Features
- **Hour 1 Theory:** Sliding window → region proposals (R-CNN, Fast R-CNN, Faster R-CNN) → single-shot detectors (SSD, YOLO). YOLO: divide image into grid, predict boxes + confidence + class. Anchor boxes. Non-maximum suppression. Feature Pyramid Networks (FPN) for multi-scale detection. IoU, mAP metrics. YOLO v5/v8 improvements.
- **Hour 2 Code:** Implement NMS from scratch. Implement IoU computation. Build a simplified YOLO-style detection head. Understand FPN architecture.
- **Hour 3 Challenge:** Build a simple object detector that can locate and classify objects in images. **Interview Q:** "Design a real-time visual quality inspection system for a manufacturing line processing 60 frames/second. Discuss model architecture, hardware, and failure modes."

### Day 042 — Image Segmentation & Transfer Learning
- **Hour 1 Theory:** Semantic vs instance vs panoptic segmentation. U-Net architecture: encoder-decoder with skip connections. Dice loss for segmentation: $\text{Dice} = \frac{2|A \cap B|}{|A| + |B|}$. Transfer learning: feature extraction vs fine-tuning. When pretrained features transfer (and when they don't). Domain adaptation theory.
- **Hour 2 Code:** Implement U-Net from scratch. Fine-tune a pretrained ResNet on a small custom dataset. Implement progressive unfreezing and discriminative learning rates.
- **Hour 3 Challenge:** Build a medical image segmentation pipeline with data augmentation. **Interview Q:** "You have 500 labeled medical images. Design a complete training strategy including pretraining, augmentation, semi-supervised learning, and evaluation."

---

## Week 7–8: Recurrent Networks & Sequence Modeling (Days 43–55)

### Day 043 — Vanilla RNN: Architecture & Backpropagation Through Time
- **Hour 1 Theory:** Hidden state recursion: $h_t = \tanh(W_{hh}h_{t-1} + W_{xh}x_t + b)$. Unrolling through time. BPTT derivation. Vanishing gradient: $\frac{\partial h_T}{\partial h_1} = \prod_{t=1}^{T-1} W_{hh}^T \text{diag}(\tanh'(z_t))$. Exploding gradient and gradient clipping. Truncated BPTT.
- **Hour 2 Code:** Implement vanilla RNN from scratch. Train on character-level language modeling (Shakespeare). Demonstrate vanishing gradients with long sequences.
- **Hour 3 Challenge:** Build a name generator using your RNN implementation. **Interview Q:** "Mathematically prove why vanilla RNNs cannot learn dependencies beyond ~10 timesteps."

### Day 044 — LSTM: Gating Mechanisms Deep Dive
- **Hour 1 Theory:** LSTM gates: forget gate $f_t = \sigma(W_f [h_{t-1}, x_t] + b_f)$, input gate $i_t = \sigma(W_i [h_{t-1}, x_t] + b_i)$, cell state update $\tilde{C}_t = \tanh(W_C [h_{t-1}, x_t] + b_C)$, output gate $o_t$. Cell state as "gradient highway." Peephole connections. Why forget gate bias should be initialized to 1. LSTM as a differentiable computer.
- **Hour 2 Code:** Implement LSTM cell from scratch in PyTorch. Train on a longer sequence task. Compare gradient flow with vanilla RNN using gradient norm plots.
- **Hour 3 Challenge:** Build a sentiment analysis model using your LSTM. **Interview Q:** "Walk through the gradient flow in an LSTM. Why does the cell state solve vanishing gradients? When does it still fail?"

### Day 045 — GRU & Bidirectional RNNs
- **Hour 1 Theory:** GRU: update gate $z_t = \sigma(W_z[h_{t-1}, x_t])$, reset gate $r_t = \sigma(W_r[h_{t-1}, x_t])$, candidate $\tilde{h}_t = \tanh(W[r_t \odot h_{t-1}, x_t])$. GRU vs LSTM: fewer parameters, similar performance. Bidirectional RNNs: concatenate forward and backward hidden states. Deep RNNs: stacking recurrent layers.
- **Hour 2 Code:** Implement GRU and Bidirectional LSTM from scratch. Compare with LSTM on a benchmark task.
- **Hour 3 Challenge:** Build a part-of-speech tagger using Bidirectional LSTM-CRF. **Interview Q:** "You're building a real-time speech recognition system. Why can't you use bidirectional RNNs? What alternatives exist?"

### Day 046 — Seq2Seq Models & the Bottleneck Problem
- **Hour 1 Theory:** Encoder-decoder architecture. Information bottleneck of fixed-size context vector. Teacher forcing: training vs inference mismatch (exposure bias). Scheduled sampling. Beam search decoding: $\hat{y} = \arg\max_y \sum_t \log p(y_t | y_{<t}, x)$. Beam width trade-offs. Length normalization.
- **Hour 2 Code:** Implement seq2seq model for machine translation (English→French on small dataset). Implement beam search with length normalization.
- **Hour 3 Challenge:** Build a date format converter using seq2seq (e.g., "January 5, 2023" → "2023-01-05"). **Interview Q:** "Your seq2seq translation model works well on short sentences but degrades on long ones. Diagnose the root cause and propose solutions."

### Day 047 — Attention Mechanism: Bahdanau & Luong
- **Hour 1 Theory:** Bahdanau (additive) attention: $e_{ij} = v^T \tanh(W_1 h_i + W_2 s_j)$, $\alpha_{ij} = \text{softmax}(e_{ij})$, context $c_j = \sum_i \alpha_{ij} h_i$. Luong (multiplicative) attention: $e_{ij} = h_i^T W s_j$. Attention as soft dictionary lookup. Computational cost: $O(nm)$. Local vs global attention. Monotonic attention.
- **Hour 2 Code:** Implement both attention mechanisms. Add attention to your Day 46 seq2seq model. Visualize attention heatmaps.
- **Hour 3 Challenge:** Build a question answering system using attention over a context paragraph. **Interview Q:** "Attention was the breakthrough that enabled Transformers. Explain the mathematical connection between Bahdanau attention and self-attention."

### Day 048 — Word Embeddings: Word2Vec, GloVe, FastText
- **Hour 1 Theory:** Distributional hypothesis ("you shall know a word by the company it keeps"). Word2Vec Skip-gram objective: $\max \sum_{t} \sum_{-c \leq j \leq c, j \neq 0} \log p(w_{t+j}|w_t)$. Negative sampling: $\log \sigma(v_{w_O}^T v_{w_I}) + \sum_{i=1}^k \mathbb{E}_{w_i \sim P_n}[\log \sigma(-v_{w_i}^T v_{w_I})]$. CBOW vs Skip-gram. GloVe: co-occurrence matrix factorization. FastText: subword embeddings for OOV handling.
- **Hour 2 Code:** Implement Skip-gram with negative sampling from scratch. Train on a text corpus. Visualize embeddings with t-SNE. Test word analogies.
- **Hour 3 Challenge:** Build a word analogy solver and compare your embeddings against pre-trained GloVe. **Interview Q:** "Word2Vec learns 'king - man + woman = queen.' Mathematically, what is this operation doing in the embedding space, and why does it work?"

### Day 049 — Subword Tokenization: BPE, WordPiece, SentencePiece
- **Hour 1 Theory:** Why word-level tokenization fails (OOV, vocabulary size). Byte Pair Encoding: iterative merging of most frequent pairs. WordPiece: likelihood-based merging. Unigram model (SentencePiece). Byte-level BPE (GPT-2). Tokenizer properties that affect LLM quality: fertility, character coverage, compression ratio.
- **Hour 2 Code:** Implement BPE tokenizer from scratch. Train on a corpus. Compare with HuggingFace tokenizers (BertTokenizer, GPT2Tokenizer). Measure tokenization efficiency.
- **Hour 3 Challenge:** Build a complete tokenizer with BPE training, encoding, and decoding. **Interview Q:** "The tokenizer is arguably the most underrated component of an LLM. Explain how tokenizer quality affects model performance, multilingual capability, and inference cost."

### Day 050 — Sequence Labeling: CRF Layer & Viterbi Decoding
- **Hour 1 Theory:** Named Entity Recognition (NER) as sequence labeling. BIO/BILOU tagging schemes. Linear-chain CRF: $P(y|x) = \frac{1}{Z(x)}\exp\left(\sum_t \psi(y_t, y_{t-1}, x)\right)$. Partition function computation with forward algorithm. Viterbi decoding for MAP inference: dynamic programming to find $\arg\max_y P(y|x)$. BiLSTM-CRF architecture.
- **Hour 2 Code:** Implement a CRF layer in PyTorch with forward algorithm for training and Viterbi for inference. Build BiLSTM-CRF for NER on CoNLL-2003 dataset.
- **Hour 3 Challenge:** Build a complete NER system from scratch with entity-level F1 evaluation. **Interview Q:** "Your NER system works well on formal text but fails on social media. Diagnose and propose three solutions that don't require labeled social media data."

### Day 051 — Text Classification: TextCNN, Hierarchical Attention Networks
- **Hour 1 Theory:** TextCNN (Kim, 2014): multiple filter sizes as n-gram detectors, max-over-time pooling. Hierarchical Attention Network (HAN): word-level attention → sentence representation → sentence-level attention → document representation. Why hierarchical models work for long documents. Comparison: CNN vs RNN vs Transformer for classification.
- **Hour 2 Code:** Implement TextCNN from scratch. Implement HAN with dual attention layers. Compare both on IMDB sentiment dataset.
- **Hour 3 Challenge:** Build a multi-label text classifier for a news dataset with per-label thresholds. **Interview Q:** "You're building a content moderation system processing 1M posts/hour. Compare architectures for latency, accuracy, and operational cost. How do you handle emerging categories?"

### Day 052 — Language Modeling: N-gram to Neural, Perplexity
- **Hour 1 Theory:** N-gram language models: $P(w_t|w_{t-n+1:t-1})$. Smoothing: Laplace, Kneser-Ney. Neural language model (Bengio et al., 2003). Perplexity: $\text{PPL} = \exp\left(-\frac{1}{N}\sum_{i=1}^N \log p(w_i|w_{<i})\right)$. Relationship to cross-entropy: $\text{PPL} = 2^{H(p,q)}$. Why perplexity matters as an evaluation metric. Bits-per-character (BPC) for character-level models.
- **Hour 2 Code:** Implement trigram language model with Kneser-Ney smoothing. Implement neural language model (single-layer LSTM). Compare perplexity on Penn Treebank.
- **Hour 3 Challenge:** Build a text autocomplete system using your language models. **Interview Q:** "GPT-4 has a perplexity of ~X on benchmark Y. What does this number actually tell you, and what doesn't it tell you? How would you evaluate an LLM beyond perplexity?"

### Day 053 — Machine Translation Evaluation & Data Augmentation
- **Hour 1 Theory:** BLEU score: $\text{BLEU} = BP \cdot \exp\left(\sum_{n=1}^N w_n \log p_n\right)$ with brevity penalty. METEOR: unigram matching with synonyms, stemming. chrF: character-level F-score. BERTScore: contextual embedding similarity. COMET: learned metric. Human evaluation protocols. Back-translation for data augmentation. Paraphrase generation.
- **Hour 2 Code:** Implement BLEU and chrF from scratch. Compute BERTScore using the library. Build a back-translation augmentation pipeline.
- **Hour 3 Challenge:** Evaluate your Day 46 translation model with all metrics and analyze where they disagree. **Interview Q:** "BLEU score correlates poorly with human judgment for some language pairs. Design an evaluation strategy for a production translation system serving 50 language pairs."

### Day 054 — Speech & Audio Processing: Mel Spectrograms & CTC
- **Hour 1 Theory:** Audio as waveform. Short-Time Fourier Transform (STFT). Mel scale: $m = 2595 \log_{10}(1 + f/700)$. Mel spectrogram computation. MFCC features. Connectionist Temporal Classification (CTC): $P(y|x) = \sum_{\pi \in \mathcal{B}^{-1}(y)} \prod_t p(\pi_t|x)$ with blank symbol and collapsing function. CTC loss for alignment-free training.
- **Hour 2 Code:** Implement mel spectrogram computation from scratch using STFT. Implement CTC decoding (greedy and beam search). Build a simple speech command classifier.
- **Hour 3 Challenge:** Build a keyword spotting system (e.g., "hey assistant") using mel spectrograms + CNN. **Interview Q:** "Design a real-time speech-to-text pipeline for a call center processing 10K concurrent calls. Discuss streaming architecture, model selection, and error handling."

### Day 055 — Phase 2 Mid-Review: Complete NLP Pipeline & Time Series
- **Hour 1 Theory:** Full NLP pipeline review: text preprocessing (tokenize → normalize → embed → encode → classify). Time series fundamentals: stationarity, autocorrelation, seasonal decomposition. AR, MA, ARIMA models. Time series with neural networks: 1D CNN, LSTM for forecasting. Temporal convolutional networks (TCN). Proper time-series cross-validation (walk-forward).
- **Hour 2 Code:** Build a complete NLP pipeline (tokenize → BPE → embed → BiLSTM+attention → classify). Build a time-series forecaster using LSTM on a stock/weather dataset with proper temporal splits.
- **Hour 3 Challenge:** Combine both: build a sentiment-driven time-series prediction system (predict stock movement from news sentiment). **Interview Q:** "You're asked to forecast demand for 100K products across 500 stores, each with different seasonality. Describe your approach including feature engineering, model selection, and handling cold-start products."

---

## Days 56–60: Generative Models

### Day 056 — Autoencoders & Variational Autoencoders (VAE)
- **Hour 1 Theory:** Autoencoder: encoder $z = f_\theta(x)$, decoder $\hat{x} = g_\phi(z)$. Denoising autoencoders. Sparse autoencoders. VAE: $\mathcal{L} = \mathbb{E}_{q_\phi(z|x)}[\log p_\theta(x|z)] - D_{KL}(q_\phi(z|x) \| p(z))$. Reparameterization trick: $z = \mu + \sigma \odot \epsilon, \epsilon \sim \mathcal{N}(0,I)$. ELBO derivation from scratch. Posterior collapse problem.
- **Hour 2 Code:** Implement VAE from scratch in PyTorch. Train on MNIST. Visualize latent space and generated samples. Implement latent space interpolation. Implement KL annealing to combat posterior collapse.
- **Hour 3 Challenge:** Build a conditional VAE (CVAE) that generates digits conditioned on class label. **Interview Q:** "Derive the ELBO for a VAE and explain the 'posterior collapse' problem. How do $\beta$-VAE and KL annealing address this?"

### Day 057 — GANs: Theory, Training Dynamics & Mode Collapse
- **Hour 1 Theory:** Minimax game: $\min_G \max_D \mathbb{E}_{x \sim p_{data}}[\log D(x)] + \mathbb{E}_{z \sim p_z}[\log(1-D(G(z)))]$. Nash equilibrium. Mode collapse: generator produces limited diversity. Training instabilities: oscillation, vanishing gradients for generator. Wasserstein distance and WGAN: $W(p_r, p_g) = \inf_{\gamma \in \Pi(p_r,p_g)} \mathbb{E}_{(x,y)\sim\gamma}[\|x-y\|]$. Gradient penalty. Progressive growing. StyleGAN overview.
- **Hour 2 Code:** Implement DCGAN from scratch. Train on CIFAR-10. Implement gradient penalty (WGAN-GP). Track FID score.
- **Hour 3 Challenge:** Build a conditional GAN (cGAN) for class-conditional image generation. **Interview Q:** "Compare GANs, VAEs, and diffusion models across: sample quality, training stability, mode coverage, and latent space properties."

### Day 058 — Diffusion Models: DDPM Fundamentals
- **Hour 1 Theory:** Forward process: $q(x_t|x_{t-1}) = \mathcal{N}(x_t; \sqrt{1-\beta_t}x_{t-1}, \beta_t I)$. Closed form: $q(x_t|x_0) = \mathcal{N}(x_t; \sqrt{\bar{\alpha}_t}x_0, (1-\bar{\alpha}_t)I)$. Reverse process: $p_\theta(x_{t-1}|x_t)$. Training objective simplified to $\mathcal{L} = \mathbb{E}_{t,x_0,\epsilon}[\|\epsilon - \epsilon_\theta(x_t, t)\|^2]$. Noise schedule (linear, cosine). Connection to score matching: $\nabla_x \log p(x)$. DDIM: deterministic sampling.
- **Hour 2 Code:** Implement DDPM from scratch: noise scheduler (linear + cosine), U-Net denoiser with time embedding, training loop, sampling loop. Implement DDIM sampling for faster generation.
- **Hour 3 Challenge:** Train DDPM on a simple dataset and generate samples. Implement classifier-free guidance. **Interview Q:** "Stable Diffusion uses a latent diffusion model. Explain the architecture and why operating in latent space is critical for computational efficiency."

### Day 059 — Graph Neural Networks: GCN, GAT, GraphSAGE
- **Hour 1 Theory:** Message passing framework: $h_v^{(k)} = \text{UPDATE}(h_v^{(k-1)}, \text{AGGREGATE}(\{h_u^{(k-1)} : u \in \mathcal{N}(v)\}))$. GCN: $H^{(l+1)} = \sigma(\tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}H^{(l)}W^{(l)})$. GAT: attention-weighted aggregation. GraphSAGE: sampling + aggregation for scalability. Over-smoothing problem in deep GNNs. WL test and GNN expressiveness.
- **Hour 2 Code:** Implement GCN from scratch using adjacency matrices. Train on Cora citation dataset for node classification. Implement GAT attention.
- **Hour 3 Challenge:** Build a simple molecular property predictor using GNN on SMILES strings. **Interview Q:** "Design a GNN-based recommendation system for a social network with 1B users. Discuss scalability, mini-batching on graphs, and real-time inference."

### Day 060 — Phase 2 Capstone: Build a Complete Deep Learning System
- **Hour 1 Theory:** Review all Phase 2 architectures. Understand the evolution: MLP → CNN → RNN → Attention → Transformers. Why each step was necessary. Self-supervised learning paradigm: pretext tasks (rotation prediction, contrastive learning, masked prediction). SimCLR, BYOL, DINO overview.
- **Hour 2 Code:** Build a multi-modal system: image encoder (CNN) + text encoder (LSTM with attention) → combined classifier. Implement contrastive learning objective.
- **Hour 3 Challenge:** Design and implement from memory. **Interview Q:** "You're the architect for a new multi-modal AI system at scale. Discuss the architecture, training strategy, serving infrastructure, and team structure."

---

# ═══════════════════════════════════════════════════════════════
# PHASE 3: TRANSFORMERS & MODERN NLP
# Days 061–090 | "Attention Is All You Need"
# ═══════════════════════════════════════════════════════════════

> **Phase Objective:** Deeply understand every component of the Transformer architecture. Implement it from scratch. Then master BERT, GPT, T5, Vision Transformers, modern efficiency techniques, and production RAG systems.

### Phase 3 Milestone Checklist
- [ ] Can implement a full Transformer (encoder + decoder) from scratch in PyTorch
- [ ] Can explain every component: self-attention, MHA, FFN, positional encoding, normalization
- [ ] Can implement RoPE, GQA, SwiGLU, KV-cache
- [ ] Can build a working RAG system with vector search + reranking
- [ ] Can fine-tune BERT/GPT on downstream tasks using HuggingFace
- [ ] Can compare Flash Attention, linear attention, and sparse attention trade-offs

---

## Week 9–10: The Transformer Architecture (Days 61–72)

### Day 061 — Self-Attention: The Core Innovation
- **Hour 1 Theory:** Queries, Keys, Values: $\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$. Why $\sqrt{d_k}$ scaling (variance of dot products grows with dimension: if $q, k \sim \mathcal{N}(0,1)$, then $q \cdot k$ has variance $d_k$). Attention as soft dictionary lookup. Computational complexity: $O(n^2 d)$. Comparison with recurrence: $O(nd^2)$ but parallelizable. Attention as kernel regression.
- **Hour 2 Code:** Implement scaled dot-product attention from scratch. Visualize attention weights for sample sentences. Verify against `torch.nn.functional.scaled_dot_product_attention`.
- **Hour 3 Challenge:** Implement attention with masking (causal + padding masks). **Interview Q:** "Derive the scaling factor $\sqrt{d_k}$ from first principles. What happens to gradient flow through softmax without it?"

### Day 062 — Multi-Head Attention: Parallel Subspace Projections
- **Hour 1 Theory:** Multi-head: $\text{MHA}(Q,K,V) = \text{Concat}(\text{head}_1,...,\text{head}_h)W^O$ where $\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$. Why multiple heads: learning different types of relationships (positional, syntactic, semantic). Head dimension: $d_k = d_{model}/h$. Multi-Query Attention (MQA): shared K,V projections. Grouped Query Attention (GQA) as used in LLaMA 2: intermediate between MHA and MQA.
- **Hour 2 Code:** Implement Multi-Head Attention from scratch. Implement GQA. Visualize what different attention heads learn (attention pattern analysis).
- **Hour 3 Challenge:** Implement Multi-Head Attention supporting standard, MQA, and GQA modes with a single codebase. **Interview Q:** "LLaMA 2 uses Grouped Query Attention. Explain the KV-cache memory savings compared to standard MHA and MQA. Derive the exact memory reduction for a 70B parameter model."

### Day 063 — Positional Encoding: Sinusoidal, Learned & RoPE
- **Hour 1 Theory:** Why position matters (attention is permutation-invariant by design). Sinusoidal encoding: $PE_{(pos,2i)} = \sin(pos/10000^{2i/d})$, $PE_{(pos,2i+1)} = \cos(pos/10000^{2i/d})$. Properties: unique encoding, bounded, captures relative position via rotation matrix. Learned positional embeddings (BERT). ALiBi: attention bias instead of embedding. Rotary Position Embeddings (RoPE): $f(x_m, m) = R_{\Theta,m} x_m$ where $R$ is a block-diagonal rotation matrix. Why RoPE enables better length generalization. NTK-aware scaling and YaRN for context extension.
- **Hour 2 Code:** Implement sinusoidal PE, learned PE, and RoPE from scratch. Visualize the encodings as heatmaps. Show that sinusoidal PE allows relative position computation via dot product.
- **Hour 3 Challenge:** Implement RoPE and integrate it into your MHA from Day 62. **Interview Q:** "Your LLM was trained with 4K context but users need 32K. Compare positional encoding approaches for length extrapolation: ALiBi, RoPE with NTK-aware scaling, YaRN."

### Day 064 — Feed-Forward Network, Residual Connections & Layer Norm
- **Hour 1 Theory:** Position-wise FFN: $\text{FFN}(x) = W_2 \cdot \text{activation}(W_1 x + b_1) + b_2$. Hidden dimension typically $4 \times d_{model}$. SwiGLU variant (LLaMA): $\text{SwiGLU}(x) = (\text{Swish}(xW_1) \odot xV)W_2$. GeGLU variant (PaLM). Pre-norm vs post-norm: $y = x + \text{Sublayer}(\text{LN}(x))$ vs $y = \text{LN}(x + \text{Sublayer}(x))$. Why pre-norm is more stable for deep models (gradient flow analysis). DeepNorm for very deep Transformers.
- **Hour 2 Code:** Implement FFN with GELU and SwiGLU variants. Implement a full Transformer encoder block with pre-norm residual connections. Compare parameter counts.
- **Hour 3 Challenge:** Build a complete Transformer encoder block from scratch. **Interview Q:** "SwiGLU has 50% more parameters than standard FFN for the same hidden size. How does LLaMA compensate, and why is SwiGLU worth the cost?"

### Day 065 — The Complete Transformer Encoder
- **Hour 1 Theory:** Stack of $N$ identical encoder layers. Input embedding (scaled by $\sqrt{d_{model}}$) + positional encoding → N × (Multi-Head Self-Attention + FFN with residual + LayerNorm) → output representations. Information flow and gradient paths. Effective receptive field grows with depth. Attention sink phenomenon.
- **Hour 2 Code:** Implement the complete Transformer encoder stack. Build a text classification model using the encoder with [CLS] token pooling.
- **Hour 3 Challenge:** Train your Transformer encoder on IMDB sentiment analysis from scratch (small model). **Interview Q:** "Your Transformer encoder's attention layers are the bottleneck. Propose three different strategies to reduce computational cost while preserving quality."

### Day 066 — The Transformer Decoder & Causal Masking
- **Hour 1 Theory:** Decoder layers: masked self-attention (causal mask) + cross-attention + FFN. Causal mask: upper triangular matrix of $-\infty$. Autoregressive generation: $p(y_1,...,y_T) = \prod_{t=1}^T p(y_t|y_{<t})$. KV-cache: avoiding redundant computation during generation — store K,V from previous timesteps, only compute new token's Q. Memory-time tradeoff.
- **Hour 2 Code:** Implement the complete Transformer decoder with causal masking and KV-cache for efficient inference. Profile the speedup from KV-cache.
- **Hour 3 Challenge:** Build a character-level text generator using your Transformer decoder. **Interview Q:** "Derive the FLOPs savings of KV-cache during autoregressive generation. For a model with $L$ layers, $d$ model dimension, and sequence length $n$, what's the memory cost?"

### Day 067 — Full Transformer: Encoder-Decoder Architecture
- **Hour 1 Theory:** Original "Attention Is All You Need" architecture. Cross-attention: decoder queries attend to encoder keys/values. Encoder-decoder vs decoder-only vs encoder-only — when to use each. Label smoothing in Transformers. Attention dropout, residual dropout. Weight tying (embedding and output projection).
- **Hour 2 Code:** Implement the complete Transformer (encoder + decoder) for machine translation. Include all components: embedding, positional encoding, N encoder layers, N decoder layers, output projection with weight tying.
- **Hour 3 Challenge:** Train your Transformer on a translation dataset and evaluate with BLEU. **Interview Q:** "GPT is decoder-only, BERT is encoder-only, T5 is encoder-decoder. Explain the architectural trade-offs and why the industry has converged on decoder-only for LLMs."

### Day 068 — BERT: Bidirectional Representations & Pre-training
- **Hour 1 Theory:** BERT architecture (encoder-only, 12/24 layers). Pre-training objectives: Masked Language Modeling (MLM) — mask 15% of tokens (80% [MASK], 10% random, 10% unchanged), predict them. Next Sentence Prediction (NSP) — later shown unnecessary (RoBERTa). [CLS] token for classification, [SEP] for segment separation. Fine-tuning paradigm: add task-specific head. RoBERTa improvements: more data, no NSP, dynamic masking, larger batches.
- **Hour 2 Code:** Implement BERT architecture from scratch. Implement MLM pre-training objective. Fine-tune HuggingFace BERT on a downstream task (SST-2 sentiment classification).
- **Hour 3 Challenge:** Pre-train a small BERT (4 layers, 256 dim) on a text corpus and fine-tune for classification. Compare with fine-tuning the full HuggingFace BERT. **Interview Q:** "BERT revolutionized NLP. Explain the pre-train/fine-tune paradigm shift. Why was bidirectional context a breakthrough, and what are BERT's limitations?"

### Day 069 — GPT: Autoregressive Language Modeling
- **Hour 1 Theory:** GPT architecture (decoder-only). Autoregressive pre-training: $\mathcal{L} = -\sum_t \log p(x_t|x_{<t})$. GPT-2 scaling: 1.5B parameters, "zero-shot" task performance. GPT-3: 175B parameters, in-context learning, few-shot prompting. Emergent abilities with scale. Scaling laws (Kaplan et al.): $L(N) = (N_c/N)^{\alpha_N}$. Chinchilla optimal: $N \propto C^{0.5}$, $D \propto C^{0.5}$.
- **Hour 2 Code:** Implement GPT-2 architecture from scratch in PyTorch. Load pretrained weights from HuggingFace. Generate text with temperature, top-k, top-p (nucleus) sampling, and repetition penalty.
- **Hour 3 Challenge:** Implement temperature, top-k, top-p, and repetition penalty decoding strategies from scratch. Compare sample quality. **Interview Q:** "Explain Chinchilla scaling laws. Given a compute budget of $10^{23}$ FLOPs, what is the optimal model size and training token count?"

### Day 070 — T5, Encoder-Decoder Models & Instruction Tuning
- **Hour 1 Theory:** T5: text-to-text framework ("translate English to German: ..."). Sentinel tokens for span corruption. Relative position bias instead of absolute PE. Comparison of pre-training objectives across T5 paper (prefix LM, BERT-style, deshuffling). Instruction tuning: Flan-T5, Flan-PaLM. How instruction tuning enables zero-shot generalization.
- **Hour 2 Code:** Fine-tune a T5 model for summarization using HuggingFace. Implement relative position bias from scratch. Fine-tune Flan-T5 for a custom task.
- **Hour 3 Challenge:** Build a question-answering system using T5 with custom prompting. **Interview Q:** "Compare the text-to-text paradigm with task-specific heads. What are the production trade-offs in terms of model management, serving, and cost?"

### Day 071 — Vision Transformer (ViT) & Multi-Modal Architectures
- **Hour 1 Theory:** ViT: split image into patches → linear projection → position embedding → Transformer encoder. Patch embedding as convolution: $\text{patch} = \text{Conv2d}(3, d, \text{kernel}=P, \text{stride}=P)$. Why ViT needs more data than CNNs (lacks inductive bias of locality and translation equivariance). DeiT: data-efficient training with distillation. CLIP: contrastive pre-training of vision + language with InfoNCE. SigLIP: sigmoid loss for CLIP (no need for in-batch negatives).
- **Hour 2 Code:** Implement ViT from scratch. Train on CIFAR-10. Load CLIP and compute image-text similarity scores.
- **Hour 3 Challenge:** Build an image search engine using CLIP embeddings with FAISS indexing. **Interview Q:** "Design a visual search system for an e-commerce platform with 100M products. Discuss embedding generation, indexing (FAISS/ScaNN), and serving architecture."

### Day 072 — Efficient Attention: Flash Attention, Linear Attention, Sparse Attention
- **Hour 1 Theory:** Standard attention: $O(n^2)$ memory and compute. Memory hierarchy: SRAM (fast, small) vs HBM (slow, large). Flash Attention: tiling and recomputation to reduce HBM access from $O(n^2)$ to $O(n)$. IO-aware algorithm design. Flash Attention 2 & 3 improvements. Linear attention: $\text{Attention}(Q,K,V) = \phi(Q)(\phi(K)^TV)$ — kernel trick to avoid materializing $n \times n$ matrix. Sparse attention patterns: local window, strided, BigBird (global + sliding window + random).
- **Hour 2 Code:** Implement standard attention with explicit memory tracking. Use Flash Attention via `torch.nn.functional.scaled_dot_product_attention`. Benchmark memory and speed. Implement sliding window attention.
- **Hour 3 Challenge:** Implement a simple local-window attention pattern and compare with full attention on a long-sequence task. **Interview Q:** "Flash Attention achieves 2-4x speedup without approximation. Explain the tiling algorithm and why it's IO-bound rather than compute-bound on modern GPUs."

---

## Days 73–90: Advanced Transformer Topics & RAG

### Day 073 — Tokenizer Engineering: Design, Training & Vocabulary Optimization
- **Hour 1 Theory:** Vocabulary size trade-offs (compression ratio vs. embedding table size). Tokenizer training data composition and its effect on model quality. Multilingual tokenization challenges (fertility disparity). Byte-level fallback. Special tokens: [BOS], [EOS], [PAD], [UNK], [MASK]. Tokenizer-model co-design. Measuring tokenizer quality: compression ratio, fertility across languages.
- **Hour 2 Code:** Train a custom BPE tokenizer using HuggingFace `tokenizers` library. Analyze vocabulary distribution. Compare tokenization efficiency across languages. Implement custom special token handling.
- **Hour 3 Challenge:** Design and train a tokenizer optimized for a specific domain (e.g., code, medical text). Measure improvements. **Interview Q:** "You're building a multilingual LLM. English uses 1.2 tokens/word but Hindi uses 3.5 tokens/word. How does this affect cost, quality, and user experience? How do you fix it?"

### Day 074 — Pre-training at Scale: Data, Compute & Infrastructure
- **Hour 1 Theory:** Pre-training data pipeline: crawling → deduplication (MinHash near-dedup, exact dedup) → quality filtering (perplexity filter, classifier) → PII removal → decontamination. Data mixing: web, books, code, scientific papers, conversations. Optimal ratios (Llama paper findings). Compute requirements: $C \approx 6ND$ (N = params, D = tokens). Training stability: loss spikes, gradient norms, learning rate restarts.
- **Hour 2 Code:** Build a data processing pipeline: download text, deduplicate with MinHash (datasketch library), filter with a quality classifier, tokenize, and create training shards.
- **Hour 3 Challenge:** Process a small web crawl dataset through your full pipeline. **Interview Q:** "You have a budget to train a 13B parameter model. Walk through every decision: data collection, cleaning, tokenizer training, model architecture, training infrastructure, and evaluation. What could go wrong?"

### Day 075 — Transfer Learning Strategies & Domain Adaptation
- **Hour 1 Theory:** Transfer learning taxonomy: feature extraction, fine-tuning, adapter methods. Domain adaptation: source domain ≠ target domain. Distribution shift types: covariate shift, label shift, concept drift. Unsupervised domain adaptation (DANN, domain-adversarial training). Few-shot learning: prototypical networks, matching networks. Meta-learning: MAML overview.
- **Hour 2 Code:** Implement domain-adversarial training for sentiment classification across product categories. Implement prototypical networks for few-shot classification.
- **Hour 3 Challenge:** Adapt a model trained on news text to work on legal documents with minimal labeled data. **Interview Q:** "Your production NLP model was trained on 2023 data but language has shifted (new slang, events). Design a continuous adaptation system that doesn't require full retraining."

### Day 076 — Knowledge Distillation: DistilBERT, TinyBERT & Beyond
- **Hour 1 Theory:** Knowledge distillation: student mimics teacher's soft predictions. KD loss: $\mathcal{L}_{KD} = \alpha T^2 \cdot D_{KL}(p_T(x/T) \| p_S(x/T)) + (1-\alpha) \cdot \mathcal{L}_{CE}(y, p_S(x))$. Temperature $T$ controls softness of distributions. DistilBERT: 6 layers from 12, 97% performance. TinyBERT: attention transfer + embedding transfer. Feature-based vs response-based distillation. Distillation for LLMs: challenges of scale.
- **Hour 2 Code:** Implement knowledge distillation for a BERT model. Train a 4-layer student from a 12-layer teacher. Implement attention transfer loss. Compare accuracy, latency, and model size.
- **Hour 3 Challenge:** Distill a fine-tuned BERT into a model 4x smaller with <3% accuracy loss. **Interview Q:** "You need to deploy a model on edge devices with 100MB limit. Your best model is 1.2GB. Design the complete model compression strategy: distillation, pruning, quantization. What's the expected quality-size trade-off curve?"

### Day 077 — Model Pruning: Unstructured, Structured & Movement Pruning
- **Hour 1 Theory:** Lottery Ticket Hypothesis: sparse subnetworks exist at initialization that match full network performance. Magnitude pruning: remove smallest weights. Structured pruning: remove entire neurons/channels/heads. Movement pruning: prune based on weight movement during training (better for fine-tuned models). Pruning schedules: one-shot vs. iterative. Sparse matrix formats: CSR, CSC, block-sparse.
- **Hour 2 Code:** Implement magnitude pruning with PyTorch's pruning utilities. Implement iterative pruning with rewinding. Measure sparsity vs. accuracy trade-off. Implement attention head pruning for BERT.
- **Hour 3 Challenge:** Achieve 90% sparsity on a model with <5% accuracy loss. **Interview Q:** "Unstructured pruning achieves higher sparsity but structured pruning gives actual speedups on hardware. Explain why and design a pruning strategy that achieves real-world latency reduction."

### Day 078 — Quantization: INT8, INT4, GPTQ, AWQ, GGUF
- **Hour 1 Theory:** Quantization fundamentals: map $\text{float} \to \text{int}$. Symmetric vs asymmetric quantization. Per-tensor vs per-channel vs per-group quantization. Calibration strategies. Post-Training Quantization (PTQ) vs Quantization-Aware Training (QAT). GPTQ: layer-wise quantization using Hessian information. AWQ: activation-aware weight quantization. GGUF format for llama.cpp. INT4 vs INT8 vs FP8 trade-offs.
- **Hour 2 Code:** Quantize a model to INT8 using PyTorch quantization. Quantize a LLM to 4-bit using GPTQ (auto-gptq library). Convert a model to GGUF format. Benchmark all variants.
- **Hour 3 Challenge:** Find the optimal quantization configuration for a 7B model that maintains >95% of original quality. **Interview Q:** "Your team needs to serve a 70B model on 2x A100-40GB. Walk through the quantization + tensor parallelism strategy. How do you validate that quantization hasn't degraded quality for your use case?"

### Day 079 — Mixture of Experts (MoE): Sparse Gating & Expert Routing
- **Hour 1 Theory:** MoE concept: replace FFN with $N$ expert FFNs + gating network. Gating: $G(x) = \text{TopK}(\text{softmax}(W_g x))$. Load balancing loss to prevent expert collapse. Mixtral architecture: 8 experts, top-2 routing. Switch Transformer: top-1 routing. Expert parallelism across GPUs. Capacity factor and dropped tokens. Why MoE gives "more parameters for free" (activated params << total params).
- **Hour 2 Code:** Implement MoE layer from scratch with top-k gating. Implement load balancing auxiliary loss. Build a small MoE Transformer and train on a language modeling task.
- **Hour 3 Challenge:** Compare a dense model vs MoE model with same FLOPs budget. **Interview Q:** "Mixtral 8x7B has 47B total parameters but only activates 13B per token. Explain the serving challenges: memory, routing overhead, expert parallelism. How does this affect batching?"

### Day 080 — State Space Models: Mamba & Selective SSMs
- **Hour 1 Theory:** Linear state space models: $h'(t) = Ah(t) + Bx(t)$, $y(t) = Ch(t) + Dx(t)$. Discretization: continuous → discrete. S4 model: structured state spaces with HiPPO initialization. Mamba: selective state spaces — input-dependent $B$, $C$, $\Delta$. Hardware-aware parallel scan algorithm. Why Mamba achieves $O(n)$ complexity vs Transformer's $O(n^2)$. Mamba-2 and hybrid architectures (Jamba).
- **Hour 2 Code:** Implement a basic SSM layer with discretization. Implement selective scan (simplified Mamba). Compare with Transformer attention on a sequence classification task. Use the mamba-ssm library for full implementation.
- **Hour 3 Challenge:** Build a small language model using Mamba blocks and compare perplexity with Transformer of similar size. **Interview Q:** "Mamba claims linear complexity, but Transformers still dominate LLMs. Why? Discuss the trade-offs between SSMs and Transformers in terms of quality, training efficiency, hardware utilization, and existing ecosystem."

### Day 081 — Long Context: Ring Attention, Context Parallelism & Infinite Context
- **Hour 1 Theory:** Long context challenges: quadratic attention, KV-cache memory explosion. Ring Attention: distribute sequence across devices, pass KV blocks in a ring. Context parallelism vs tensor parallelism vs data parallelism. Sequence parallelism: split LayerNorm/dropout across sequence dimension. Infinite context: chunked processing with recurrence (Infini-Attention). Context window extension: PI (Position Interpolation), NTK-aware RoPE scaling, YaRN, LongRoPE.
- **Hour 2 Code:** Implement position interpolation for extending context length. Benchmark a model at various context lengths (measure quality degradation). Implement chunked attention processing.
- **Hour 3 Challenge:** Extend a 4K context model to 16K and evaluate on long-document tasks. **Interview Q:** "Design a system that can answer questions over 1M token documents. Discuss chunking, retrieval, and long-context model strategies. When is RAG better than long context?"

### Day 082 — Multi-Modal Transformers: LLaVA, Flamingo & Vision-Language Models
- **Hour 1 Theory:** Multi-modal architecture patterns: early fusion (single model) vs late fusion (separate encoders). LLaVA: vision encoder (CLIP ViT) → MLP projection → LLM. Two-stage training: feature alignment → instruction tuning. Flamingo: perceiver resampler for variable-length visual inputs. Qwen-VL, InternVL architectures. Challenges: visual grounding, hallucination in vision-language models.
- **Hour 2 Code:** Build a simplified LLaVA architecture: load CLIP vision encoder, implement MLP projector, connect to a small LLM. Run inference on image+text inputs using HuggingFace LLaVA.
- **Hour 3 Challenge:** Build an image captioning system and evaluate with CIDEr/CLIPScore. **Interview Q:** "Design a document understanding system that processes PDFs with text, tables, charts, and images. Discuss OCR, layout analysis, multi-modal encoding, and the architecture for answering questions about the document."

### Day 083 — Retrieval-Augmented Generation (RAG) v1: Dense Retrieval Foundations
- **Hour 1 Theory:** RAG motivation: parametric knowledge (weights) vs non-parametric knowledge (retrieval). Dense retrieval: bi-encoder architecture $\text{sim}(q,d) = E_q(q) \cdot E_d(d)$. Embedding models: Sentence-BERT, E5, BGE, GTE. Approximate Nearest Neighbor (ANN) search: locality-sensitive hashing, HNSW graphs, IVF-PQ. FAISS index types and trade-offs. Chunking strategies: fixed-size, recursive, semantic.
- **Hour 2 Code:** Build a basic RAG system: load documents → chunk → embed (using sentence-transformers) → index with FAISS → retrieve → generate with LLM. Implement HNSW index.
- **Hour 3 Challenge:** Build a RAG system over a technical documentation corpus. Evaluate retrieval quality with recall@k. **Interview Q:** "Your RAG system retrieves relevant documents but the LLM generates answers that contradict the retrieved context. Diagnose and fix. Discuss grounding, attribution, and faithfulness evaluation."

### Day 084 — RAG v2: Hybrid Search, Reranking & Advanced Chunking
- **Hour 1 Theory:** Sparse retrieval: BM25 algorithm with TF-IDF. Hybrid search: combine dense + sparse with reciprocal rank fusion (RRF): $\text{RRF}(d) = \sum_r \frac{1}{k + r(d)}$. Cross-encoder reranking: $\text{score}(q,d) = \text{CrossEncoder}([q; d])$. Why reranking dramatically improves precision. Advanced chunking: parent-child, sliding window with overlap, semantic chunking (split at topic boundaries). Metadata filtering.
- **Hour 2 Code:** Implement BM25 from scratch. Build hybrid search with RRF. Add cross-encoder reranking (using cross-encoder models). Implement recursive text splitter with overlap.
- **Hour 3 Challenge:** Compare retrieval quality: BM25 only vs dense only vs hybrid vs hybrid+reranking. Quantify improvements. **Interview Q:** "Design a RAG system for a legal firm with 10M documents, strict access control, and citation requirements. Discuss chunking, retrieval pipeline, access-controlled indexing, and hallucination prevention."

### Day 085 — RAG v3: Advanced Patterns (HyDE, RAPTOR, Self-RAG, GraphRAG)
- **Hour 1 Theory:** HyDE (Hypothetical Document Embeddings): generate hypothetical answer, embed it, retrieve similar real documents. Query expansion and decomposition. RAPTOR: recursive abstractive processing for tree-organized retrieval (summarize chunks → cluster → summarize clusters → tree index). Self-RAG: model decides when to retrieve, critiques its own output. GraphRAG: extract entities/relationships → build knowledge graph → community detection → summarize communities → use for global queries. Adaptive retrieval: when to retrieve vs use parametric knowledge.
- **Hour 2 Code:** Implement HyDE retrieval. Implement query decomposition for multi-hop questions. Build a simple GraphRAG: extract entities with LLM → build networkx graph → community detection → generate community summaries.
- **Hour 3 Challenge:** Build a multi-hop QA system that decomposes complex questions and retrieves evidence for each sub-question. **Interview Q:** "Compare naive RAG, HyDE, RAPTOR, and GraphRAG for a customer support use case with 50K FAQ articles. Discuss retrieval quality, latency, cost, and maintenance burden."

### Day 086 — Embedding Models: Training, Evaluation & Matryoshka Embeddings
- **Hour 1 Theory:** Embedding model training: contrastive learning with hard negatives. Mining strategies: in-batch negatives, BM25 negatives, mined hard negatives. Training losses: InfoNCE, multiple negatives ranking loss, GISTEmbedLoss. Matryoshka Representation Learning: train embeddings that are useful at any truncated dimension ($d=256, 128, 64$). MTEB benchmark: massive text embedding benchmark across 8 tasks. Instruction-tuned embeddings (E5-mistral, GTE-Qwen).
- **Hour 2 Code:** Fine-tune an embedding model using sentence-transformers with contrastive learning. Evaluate on MTEB tasks. Implement Matryoshka loss wrapper. Compare embedding quality at different dimensions.
- **Hour 3 Challenge:** Train a domain-specific embedding model and demonstrate improvement over general-purpose models on your domain's retrieval task. **Interview Q:** "Your RAG system's retrieval accuracy dropped 15% after switching domains. Diagnose whether the issue is the embedding model, chunking strategy, or something else. Propose a fix."

### Day 087 — Vector Databases: FAISS, Qdrant, Weaviate, Pinecone & ChromaDB
- **Hour 1 Theory:** Vector database architecture: storage, indexing, search, filtering. FAISS: CPU/GPU indexes, IVF, PQ, HNSW, composite indexes (IVF-PQ, IVF-HNSW). Managed services: Pinecone (serverless), Weaviate (hybrid search), Qdrant (rust-based, filtering), ChromaDB (lightweight, local). Milvus for enterprise. Index build time vs query time trade-offs. Metadata filtering and hybrid queries. Scalability: sharding, replication.
- **Hour 2 Code:** Build the same retrieval system using FAISS, ChromaDB, and Qdrant (local). Compare: indexing speed, query speed, memory usage, filter support. Implement proper index selection based on dataset size.
- **Hour 3 Challenge:** Build a scalable document search system with metadata filtering, multi-tenancy, and access control. **Interview Q:** "You're building a semantic search platform for 100M documents. Compare FAISS, Qdrant, and Pinecone for this scale. Discuss indexing strategy, query latency SLAs, cost, and operational complexity."

### Day 088 — Prompt Engineering: Chain-of-Thought, Few-Shot & Advanced Techniques
- **Hour 1 Theory:** Prompt engineering as programming. Zero-shot, few-shot, many-shot prompting. Chain-of-Thought (CoT): "Let's think step by step." Zero-shot CoT vs few-shot CoT. Self-consistency: sample multiple CoT paths, majority vote. Tree of Thought: explore multiple reasoning paths with BFS/DFS. Prompt chaining and decomposition. Role prompting and persona. Prompt sensitivity and brittleness.
- **Hour 2 Code:** Implement CoT prompting for mathematical reasoning. Implement self-consistency with majority voting. Build a prompt chaining system for complex multi-step tasks. Evaluate prompt variants on GSM8K math benchmark.
- **Hour 3 Challenge:** Build a prompt optimization system that automatically tests and ranks prompt variants. **Interview Q:** "Your team has 50 different prompts across 10 products. They break every time the model is updated. Design a prompt management and testing infrastructure for enterprise scale."

### Day 089 — Structured Output: JSON Mode, Function Calling & Constrained Decoding
- **Hour 1 Theory:** Structured output challenges: LLMs generate free-form text, but applications need structured data. JSON mode: model outputs valid JSON. Function calling protocol (OpenAI, Anthropic): define function schemas, model outputs structured calls. Tool use as structured output. Constrained decoding: guide generation with finite state machines or context-free grammars. Outlines library: regex/JSON schema constraints. LMQL: SQL-like prompting language. Pydantic + LLM integration patterns.
- **Hour 2 Code:** Implement function calling with OpenAI API. Use Pydantic models with `instructor` library for guaranteed structured output. Implement basic constrained decoding with token masking. Build a data extraction pipeline (extract entities from unstructured text into structured format).
- **Hour 3 Challenge:** Build a resume parser that extracts structured information (name, education, experience) from free-form resumes using function calling. Handle edge cases. **Interview Q:** "You're building a data extraction pipeline that must process 1M documents/day into structured records with 99.5% accuracy. Design the system including model selection, validation, error handling, and human review."

### Day 090 — Phase 3 Capstone: Build a Production RAG System
- **Hour 1 Theory:** Production RAG architecture review: document ingestion pipeline → chunking → embedding → indexing → query processing → retrieval → reranking → generation → citation → evaluation. Evaluation: faithfulness (is the answer grounded?), relevance (is the answer useful?), context precision/recall. RAG evaluation frameworks: RAGAS, DeepEval. End-to-end testing strategies.
- **Hour 2 Code:** Build a complete production RAG system with: PDF/HTML document loader → recursive chunking → hybrid search (BM25 + dense) → cross-encoder reranking → LLM generation with citations → faithfulness evaluation using RAGAS.
- **Hour 3 Challenge:** Deploy your RAG system as an API and load test it. Identify and fix bottlenecks. **Interview Q:** "Design a RAG-powered enterprise knowledge base for a company with 500K internal documents across 20 departments. Cover: document processing, access control, multi-modal content, real-time updates, evaluation, and cost optimization."

---

# ═══════════════════════════════════════════════════════════════
# PHASE 4: LLMs — TRAINING, FINE-TUNING & ALIGNMENT
# Days 091–120 | "Mastering the Large Language Model Lifecycle"
# ═══════════════════════════════════════════════════════════════

> **Phase Objective:** Understand how LLMs are pre-trained, fine-tuned, and aligned. Master LoRA, QLoRA, RLHF, DPO. Build production fine-tuning pipelines. Understand LLM evaluation, safety, and security.

### Phase 4 Milestone Checklist
- [ ] Can explain the full LLM training pipeline: data → pretraining → SFT → alignment
- [ ] Can fine-tune a 7B model with QLoRA on a single GPU
- [ ] Can implement DPO training and understand its relationship to RLHF
- [ ] Can evaluate LLMs using automated benchmarks and LLM-as-judge
- [ ] Can implement speculative decoding and structured generation
- [ ] Can articulate safety/security concerns and mitigation strategies

---

## Week 13–14: LLM Pre-Training & Architecture (Days 91–100)

### Day 091 — LLM Architecture Deep Dive: LLaMA, Mistral, Gemma, Qwen
- **Hour 1 Theory:** LLaMA architecture choices: RMSNorm (pre-norm), SwiGLU FFN, RoPE, GQA. Mistral: sliding window attention (4096 window), rolling buffer cache. Gemma: differences from LLaMA (GeGLU, different normalization). Qwen: architecture variants. Parameter counting: $P \approx 12 L d^2$ (for standard Transformer). Where parameters live: embedding table, attention projections, FFN weights, normalization.
- **Hour 2 Code:** Load a LLaMA model and inspect every layer's shapes and parameter counts. Implement a parameter counter that breaks down by component. Trace a single forward pass with hooks to monitor activations.
- **Hour 3 Challenge:** Given a FLOPs budget, design an optimal LLM architecture (choose d_model, n_layers, n_heads, FFN size). **Interview Q:** "You have budget for 200B FLOPs of training. Design the model architecture and training plan using Chinchilla scaling laws. Justify every architectural choice."

### Day 092 — Pre-Training Data: Collection, Cleaning & Deduplication
- **Hour 1 Theory:** Data sources: Common Crawl (petabytes of web), Wikipedia, Books, GitHub, arXiv, StackOverflow. Processing pipeline: extraction → language detection → deduplication → quality filtering → toxicity/PII removal. MinHash for near-duplicate detection: approximate Jaccard similarity. Exact substring deduplication (suffix arrays). Quality filtering: perplexity filter using a smaller LM, URL blocklists, classifier-based filtering. Data mixing: optimal ratios of web/books/code/scientific. Dataset projects: Dolma, RedPajama, FineWeb, DCLM.
- **Hour 2 Code:** Build a data processing pipeline: download sample Common Crawl data → extract text with trafilatura → detect language → deduplicate with MinHash (datasketch) → filter with quality heuristics → tokenize and shard.
- **Hour 3 Challenge:** Process a 1GB web crawl and measure deduplication rate, quality distribution, and final dataset statistics. **Interview Q:** "You're curating training data for a 13B model. You have 5TB of raw web text. Walk through your complete data pipeline including dedup, filtering, PII scrubbing, and decontamination. How do you measure data quality?"

### Day 093 — Distributed Training: Data Parallel, Tensor Parallel, Pipeline Parallel
- **Hour 1 Theory:** Why distributed training: single GPU can't fit large models. Data Parallelism (DP/DDP): replicate model, split batch. FSDP (Fully Sharded Data Parallel): shard optimizer states, gradients, and parameters across GPUs. Tensor Parallelism (Megatron-LM): split weight matrices across GPUs. Pipeline Parallelism: split layers across GPUs, micro-batch pipelining. DeepSpeed ZeRO stages: Stage 1 (shard optimizer), Stage 2 (+ gradients), Stage 3 (+ parameters). 3D parallelism. Communication overhead: all-reduce, all-gather, reduce-scatter.
- **Hour 2 Code:** Train a model with PyTorch DDP on multiple GPUs (or simulate). Configure FSDP for a larger model. Understand DeepSpeed configuration (ZeRO Stage 2/3). Profile communication overhead.
- **Hour 3 Challenge:** Calculate the memory requirements for training a 7B model with different parallelism strategies. **Interview Q:** "You need to train a 70B model on a cluster of 256 A100-80GB GPUs. Design the parallelism strategy (data, tensor, pipeline) and estimate training time for 2T tokens."

### Day 094 — Mixed Precision Training & Memory Optimization
- **Hour 1 Theory:** FP32 (32-bit), FP16 (16-bit), BF16 (16-bit, larger range). FP16 risks: overflow (max 65504) and underflow. Loss scaling: multiply loss by scale factor, divide gradients back. BF16 advantages: same range as FP32, no loss scaling needed. Dynamic loss scaling algorithm. FP8 for inference. Gradient accumulation: simulate large batches $B_{eff} = B_{micro} \times n_{accum}$. Gradient checkpointing (activation recomputation): trade compute for memory.
- **Hour 2 Code:** Implement mixed precision training with `torch.cuda.amp`. Implement gradient accumulation. Implement gradient checkpointing with `torch.utils.checkpoint`. Profile memory savings from each technique.
- **Hour 3 Challenge:** Train a model that doesn't fit in GPU memory using the combination of mixed precision + gradient accumulation + gradient checkpointing. **Interview Q:** "Your training run produces NaN loss after 1000 steps with BF16. Diagnose the possible causes and propose fixes without switching to FP32."

### Day 095 — Training Infrastructure: GPU Clusters, NCCL & Checkpointing
- **Hour 1 Theory:** GPU cluster architecture: compute nodes, NVLink/NVSwitch (intra-node), InfiniBand/RoCE (inter-node). NCCL: NVIDIA's collective communication library. All-reduce algorithms: ring, tree, recursive halving-doubling. Checkpoint management: save frequency, async checkpointing, checkpoint size reduction. Elastic training: handle node failures. Training resumption: matching optimizer states, LR schedule. Weights & Biases / MLflow for experiment tracking at scale.
- **Hour 2 Code:** Implement robust checkpointing with async saving. Implement training resumption that correctly restores model, optimizer, scheduler, and RNG state. Set up WandB logging with custom metrics.
- **Hour 3 Challenge:** Simulate a training interruption and demonstrate clean resumption with no quality loss. **Interview Q:** "Your LLM training run on 128 GPUs crashes at step 50,000 due to a hardware failure. Describe your recovery strategy. How do you prevent data loss and minimize wasted compute?"

### Day 096 — Full Fine-Tuning vs Parameter-Efficient Fine-Tuning (PEFT)
- **Hour 1 Theory:** Full fine-tuning: update all parameters. Catastrophic forgetting: model loses pre-trained knowledge. PEFT taxonomy: Adapter layers (Houlsby et al.): small bottleneck layers inserted after attention/FFN. Prefix tuning: learnable prefix tokens prepended to keys/values. Prompt tuning: learnable continuous prompt embeddings. LoRA: low-rank updates. (IA)³: learned rescaling vectors. Comparison: parameter count, training speed, inference overhead, quality.
- **Hour 2 Code:** Implement adapter layers from scratch. Fine-tune with full fine-tuning vs adapter vs prefix tuning using PEFT library. Compare training speed, memory usage, and final quality.
- **Hour 3 Challenge:** Find the PEFT method that achieves the best quality/efficiency trade-off for a specific task. **Interview Q:** "Your company needs to fine-tune a 70B model for 20 different customers. Compare full fine-tuning, LoRA, and adapter approaches from the perspective of compute cost, storage, and serving complexity."

### Day 097 — LoRA: Low-Rank Adaptation Deep Dive
- **Hour 1 Theory:** LoRA: $W' = W + \Delta W = W + BA$ where $B \in \mathbb{R}^{d \times r}$, $A \in \mathbb{R}^{r \times d}$, $r \ll d$. Initialization: $A$ is random Gaussian, $B$ is zero (so $\Delta W = 0$ at start). Why low-rank works: weight updates during fine-tuning have low intrinsic rank (Aghajanyan et al.). Rank selection heuristics. Which modules to adapt: attention only vs all linear layers. Alpha scaling: $\Delta W = \frac{\alpha}{r} BA$. LoRA+: different learning rates for A and B. DoRA: weight-decomposed low-rank adaptation. rsLoRA: rank-stabilized scaling.
- **Hour 2 Code:** Implement LoRA from scratch as a PyTorch module. Fine-tune LLaMA-7B with LoRA using PEFT library. Merge LoRA weights back into base model for inference. Experiment with rank (4, 8, 16, 32, 64) and target modules.
- **Hour 3 Challenge:** Implement LoRA, merge weights, and verify that merged model produces identical outputs. **Interview Q:** "Explain the mathematical justification for why LoRA works. A team claims rank-4 LoRA is 'good enough' for all tasks. Under what conditions would you need higher rank?"

### Day 098 — QLoRA & Memory-Efficient Fine-Tuning
- **Hour 1 Theory:** QLoRA: 4-bit NormalFloat (NF4) quantized base model + LoRA adapters in BF16 + double quantization (quantize the quantization constants) + paged optimizers (use CPU RAM for optimizer states via unified memory). NF4 data type: optimal for normally distributed weights. Memory calculation: 65B model needs ~33GB with QLoRA vs ~130GB for full precision. Training throughput impact. EETQ, bitsandbytes internals.
- **Hour 2 Code:** Fine-tune a 7B model on a single GPU using QLoRA with bitsandbytes. Compare training loss curves with full fine-tuning and full-precision LoRA. Measure memory usage and throughput.
- **Hour 3 Challenge:** Fine-tune a 13B model on a single 24GB GPU using QLoRA. Optimize for maximum throughput. **Interview Q:** "Your startup has 4x RTX 4090 (24GB each). What's the largest model you can fine-tune, and how? Walk through the complete memory budget."

### Day 099 — Instruction Tuning & Chat Templates
- **Hour 1 Theory:** SFT (Supervised Fine-Tuning) on instruction-following data. Dataset formats: instruction-input-output (Alpaca), multi-turn conversation (ShareGPT). Chat templates: ChatML (`<|im_start|>`, `<|im_end|>`), Llama chat format (`[INST]`, `[/INST]`), Gemma format. System prompts and their effect on behavior. Tokenizer's `apply_chat_template()`. Packing: concatenate multiple short examples into one sequence for efficiency. NEFTune: add noise to embeddings during fine-tuning.
- **Hour 2 Code:** Prepare a dataset in ChatML format. Fine-tune a model using TRL's SFTTrainer with chat templates. Implement sequence packing for efficiency. Implement NEFTune.
- **Hour 3 Challenge:** Create a high-quality instruction tuning dataset (100 examples) for a specific domain and fine-tune a model on it. **Interview Q:** "LIMA shows 1000 high-quality examples can match models trained on millions. Design a data curation strategy for instruction tuning. How do you measure 'quality'?"

### Day 100 — Training Data Curation & Synthetic Data
- **Hour 1 Theory:** Data quality > data quantity (LIMA principle). Decontamination: remove test set examples from training data. Synthetic data generation: using strong models to create training data for weaker models. Evol-Instruct (WizardLM): evolve instructions for complexity. Self-Instruct: generate (instruction, input, output) triples. Orca methodology: chain-of-thought traces from teacher models. Magpie: generate SFT data from model's own distribution. Data filtering: reward model scoring, perplexity filtering, deduplication.
- **Hour 2 Code:** Generate synthetic instruction data using a strong model (GPT-4/Claude). Implement Evol-Instruct (evolve simple instructions into complex ones). Filter generated data by quality score. Fine-tune on synthetic data and evaluate.
- **Hour 3 Challenge:** Create a complete synthetic data pipeline for a domain-specific chatbot. **Interview Q:** "Your company wants to build a domain-specific LLM but has no labeled data. Design a complete data flywheel: synthetic generation → filtering → training → deployment → user feedback → data collection → iteration."

---

## Days 101–110: Alignment & RLHF

### Day 101 — Reinforcement Learning Fundamentals for RLHF
- **Hour 1 Theory:** MDP formulation: state $s$, action $a$, reward $r$, policy $\pi(a|s)$, value function $V^\pi(s) = \mathbb{E}_\pi[\sum_t \gamma^t r_t | s_0 = s]$. Policy gradient theorem: $\nabla_\theta J(\theta) = \mathbb{E}_{\pi_\theta}[\nabla_\theta \log \pi_\theta(a|s) \cdot A^\pi(s,a)]$ where $A$ is advantage. REINFORCE algorithm. Baseline for variance reduction. PPO: clipped surrogate objective $L^{CLIP} = \mathbb{E}[\min(r_t(\theta)A_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)A_t)]$. Why PPO for RLHF: stability, sample efficiency.
- **Hour 2 Code:** Implement REINFORCE on CartPole. Implement PPO with clipped objective on a simple environment. Visualize policy improvement over iterations.
- **Hour 3 Challenge:** Implement PPO from scratch and train an agent on a text-based task (e.g., maximize a reward model score for generated text). **Interview Q:** "Why does RLHF use PPO instead of simpler policy gradient methods? What are PPO's failure modes in the context of language model training?"

### Day 102 — Reward Modeling
- **Hour 1 Theory:** Bradley-Terry model for preferences: $P(y_1 \succ y_2 | x) = \sigma(r(x, y_1) - r(x, y_2))$. Training reward models: collect human comparisons $(x, y_w, y_l)$, train to predict preference. Loss: $\mathcal{L} = -\log \sigma(r(x, y_w) - r(x, y_l))$. Reward model architecture: LLM with scalar head. Reward hacking: model exploits reward model weaknesses. Reward model overoptimization (Goodhart's law). Evaluation: agreement rate with humans, distribution of scores.
- **Hour 2 Code:** Train a reward model on preference data using TRL's RewardTrainer. Analyze reward distributions. Implement reward model as a classification head on top of a pre-trained LLM.
- **Hour 3 Challenge:** Collect preference data (using a strong model as annotator), train a reward model, and analyze its behavior. Identify failure modes. **Interview Q:** "Your reward model gives high scores to verbose, sycophantic responses. How do you diagnose and fix reward hacking? Discuss evaluation strategies beyond agreement rate."

### Day 103 — RLHF Pipeline: SFT → Reward Model → PPO
- **Hour 1 Theory:** Full RLHF pipeline stages: (1) SFT on instruction data, (2) Train reward model on preferences, (3) PPO optimization. Token-level reward: $R_t = 0$ for $t < T$, $R_T = r_{reward}(x, y) - \beta \cdot D_{KL}(\pi_\theta(y|x) \| \pi_{ref}(y|x))$. KL penalty prevents over-optimization. Per-token KL: $D_{KL}^t = \log \frac{\pi_\theta(y_t|y_{<t}, x)}{\pi_{ref}(y_t|y_{<t}, x)}$. Practical challenges: training instability, reward model quality ceiling, cost of human annotation. InstructGPT paper walkthrough.
- **Hour 2 Code:** Implement the full RLHF pipeline using TRL: SFTTrainer → RewardTrainer → PPOTrainer. Train on a small model. Monitor KL divergence, reward scores, and generation quality throughout.
- **Hour 3 Challenge:** Run the full pipeline and tune the KL coefficient $\beta$ to find the quality sweet spot. **Interview Q:** "Walk through the complete RLHF pipeline for a 70B model. Estimate compute costs for each stage. Where are the bottlenecks, and what shortcuts can you take?"

### Day 104 — DPO: Direct Preference Optimization
- **Hour 1 Theory:** DPO insight: the optimal policy under RLHF can be expressed in closed form, eliminating the need for a separate reward model. DPO loss: $\mathcal{L}_{DPO} = -\mathbb{E}_{(x,y_w,y_l)}[\log\sigma(\beta(\log\frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \log\frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}))]$. Implicit reward: $r(x,y) = \beta \log \frac{\pi_\theta(y|x)}{\pi_{ref}(y|x)} + \beta \log Z(x)$. DPO vs RLHF: simpler, more stable, but potentially lower ceiling. Variants: IPO (identity preference optimization), KTO (Kahneman-Tversky optimization — no paired preferences needed), ORPO (odds ratio preference optimization — no reference model needed), SimPO (simple preference optimization).
- **Hour 2 Code:** Implement DPO training using TRL's DPOTrainer. Compare with PPO-based RLHF on the same preference data. Implement KTO (which only needs thumbs up/down, not pairwise preferences).
- **Hour 3 Challenge:** Train a model with DPO and evaluate alignment on MT-Bench and safety benchmarks. **Interview Q:** "DPO is simpler than RLHF but some labs still prefer RLHF for their frontier models. Explain the theoretical and practical trade-offs. When would you choose each?"

### Day 105 — Constitutional AI, RLAIF & Self-Improvement
- **Hour 1 Theory:** Anthropic's Constitutional AI: define principles → self-critique and revision (CAI-SL) → preference learning from AI feedback (CAI-RL). Red-teaming: systematically probing model for harmful outputs. RLAIF: replace human annotators with AI feedback. Self-play for alignment: model debates itself. Iterative self-improvement: model generates, evaluates, and trains on its own outputs. SPIN (Self-Play Fine-Tuning). Critique-Revise-Generate loops.
- **Hour 2 Code:** Implement a Constitutional AI pipeline: generate → critique against principles → revise → collect preference pairs → train with DPO. Build an automated red-teaming system using adversarial prompts.
- **Hour 3 Challenge:** Define a constitution for a customer service bot and implement the full CAI pipeline. **Interview Q:** "Your company wants to deploy an AI assistant for healthcare. Design the complete safety pipeline: constitutional principles, red-teaming methodology, guardrails, monitoring, and incident response."

### Day 106 — LLM Evaluation: Benchmarks, LLM-as-Judge & Contamination
- **Hour 1 Theory:** Evaluation taxonomy: capability (knowledge, reasoning, coding) vs alignment (helpfulness, safety). Benchmarks: MMLU (knowledge), HellaSwag (commonsense), ARC (science), TruthfulQA (factuality), HumanEval/MBPP (coding), GSM8K (math), BBH (hard reasoning). Problems: contamination (test data in training), saturation, benchmark gaming. LLM-as-Judge: MT-Bench (multi-turn), Chatbot Arena (ELO from human votes), Arena Hard Auto (automated arena). Designing fair evaluations. ELO rating mathematics.
- **Hour 2 Code:** Evaluate a model on MMLU, HumanEval, and GSM8K using lm-evaluation-harness. Implement LLM-as-Judge with pairwise comparison. Implement ELO rating calculation. Run MT-Bench evaluation.
- **Hour 3 Challenge:** Design a custom evaluation suite for a domain-specific model. Include automated and human evaluation. **Interview Q:** "Your model scores 85% on MMLU but users complain it's worse than the previous version. How do you reconcile benchmark scores with user experience? Design a comprehensive evaluation strategy."

### Day 107 — Safety, Toxicity & Responsible AI
- **Hour 1 Theory:** Harm taxonomy: hate speech, violence, self-harm, illegal activity, PII exposure, misinformation. Jailbreaking taxonomy: direct injection, indirect injection, many-shot jailbreaking, encoding attacks, roleplay attacks. Defense layers: input filtering → safety training → output filtering → monitoring. Guardrails implementation: Llama Guard, NeMo Guardrails. Content classification models. Watermarking LLM outputs. NIST AI Risk Management Framework. EU AI Act implications.
- **Hour 2 Code:** Implement a multi-layer safety system: input classifier → model with safety system prompt → output classifier → logging. Test against common jailbreak patterns. Use Llama Guard for content classification.
- **Hour 3 Challenge:** Build a comprehensive safety testing suite and evaluate your model against it. **Interview Q:** "You're the safety lead for a consumer-facing AI product with 10M users. Design the complete safety infrastructure: pre-deployment testing, runtime guardrails, incident detection, and response playbook."

### Day 108 — Model Merging: TIES, DARE, Model Soup & Task Vectors
- **Hour 1 Theory:** Weight averaging (Model Soup): average weights of models fine-tuned with different hyperparameters. Task vectors: $\tau = \theta_{ft} - \theta_{base}$. Task vector arithmetic: adding, negating, composing capabilities. TIES-Merging: trim small values → elect sign by magnitude → disjoint merge. DARE: randomly drop (reset to base) a fraction of delta weights, then rescale. SLERP: spherical linear interpolation. Merging strategies: linear, SLERP, TIES, DARE. MergeKit framework.
- **Hour 2 Code:** Merge models using MergeKit: linear merge, SLERP, TIES-DARE. Compare merged model quality against individual fine-tuned models. Implement task vector arithmetic.
- **Hour 3 Challenge:** Create a "super model" by merging 3 differently fine-tuned models and evaluate. **Interview Q:** "Model merging creates new models without additional training. When does it work and when does it fail? What are the IP/licensing implications for production use?"

### Day 109 — Continued Pre-Training & Domain Adaptation for LLMs
- **Hour 1 Theory:** Continued pre-training: extend a general LLM with domain-specific knowledge. When to continue pre-training vs fine-tuning (knowledge injection vs behavior change). Learning rate selection: typically 10-50x lower than original pre-training. Data mixing: domain data + replay of general data to prevent forgetting. Curriculum: start with more general data, increase domain concentration. Domain-specific models: CodeLlama (code), Meditron (medical), SaulLM (legal), Galactica (science).
- **Hour 2 Code:** Continue pre-training a small model on a domain-specific corpus (e.g., medical abstracts). Measure perplexity improvement on domain text. Check for catastrophic forgetting on general benchmarks.
- **Hour 3 Challenge:** Build a domain adaptation pipeline: curate domain data → continued pre-training → instruction tuning → evaluation on domain and general tasks. **Interview Q:** "A pharmaceutical company wants an LLM specialized in drug discovery. Design the complete adaptation pipeline from base model to production deployment. How do you validate scientific accuracy?"

### Day 110 — Synthetic Data Generation at Scale
- **Hour 1 Theory:** Synthetic data paradigms: (1) Strong-to-weak distillation (GPT-4 → train smaller model). (2) Self-instruct: model generates its own training data. (3) Evol-Instruct: evolve complexity of instructions. (4) Phi approach: textbook-quality synthetic data from scratch. (5) Orca: collect chain-of-thought traces. (6) UltraChat: multi-round simulated conversations. Quality filtering: reward model scoring, length filtering, diversity metrics. Contamination prevention. Legal considerations of training on model outputs.
- **Hour 2 Code:** Build a complete synthetic data generation pipeline: seed topic generation → instruction creation → response generation → quality filtering (length, coherence, reward model) → deduplication → format for training.
- **Hour 3 Challenge:** Generate 5K high-quality synthetic conversations for a specific domain. Fine-tune on them and measure improvement. **Interview Q:** "There's debate about whether training on synthetic data leads to 'model collapse.' Explain the argument, cite evidence for and against, and propose safeguards."

---

## Days 111–120: Advanced LLM Topics

### Day 111 — Speculative Decoding & Inference Optimization
- **Hour 1 Theory:** Autoregressive bottleneck: each token requires full model forward pass. Speculative decoding: small draft model generates $k$ candidates, large target model verifies in parallel. Acceptance criteria: match target distribution exactly (provably lossless). Expected acceptance length and speedup. Medusa: add multiple decode heads to target model itself. Lookahead decoding. Eagle: draft model with feature sharing. Prompt lookup decoding for repetitive content.
- **Hour 2 Code:** Implement speculative decoding from scratch: draft model generates → target model scores batch → accept/reject using algorithm. Measure speedup. Use HuggingFace's `assistant_model` parameter.
- **Hour 3 Challenge:** Find the optimal draft model size for a given target model (trade-off: draft speed vs acceptance rate). **Interview Q:** "Your LLM serving system has a latency SLA of 100ms TPOT (time per output token). The model is too slow. Compare speculative decoding, model quantization, and smaller model + distillation. Which combination would you deploy?"

### Day 112 — Structured Generation: Outlines, Guidance & Grammar Constraints
- **Hour 1 Theory:** Constrained decoding: restrict valid next tokens at each step. Finite State Machine (FSM) for regex-guided generation. Context-Free Grammar (CFG) for JSON/XML. Outlines library: compile regex/JSON schema into FSM → mask logits. Guidance: template-based generation. LMQL: SQL-like queries over LLM outputs. Token healing for prompt boundaries. Challenges: constraint-model interaction, beam search under constraints.
- **Hour 2 Code:** Use Outlines for regex-constrained generation. Implement JSON schema-guided generation. Build a structured data extraction pipeline with guaranteed valid output. Compare with OpenAI function calling.
- **Hour 3 Challenge:** Build a SQL query generator that always produces syntactically valid SQL, with schema-aware column constraints. **Interview Q:** "You need 100% valid JSON from an LLM in production. Compare three approaches: JSON mode, constrained decoding, and post-processing with retry. Discuss reliability, latency, and quality trade-offs."

### Day 113 — Tool Use & Function Calling Architecture
- **Hour 1 Theory:** Tool-augmented LLMs: model decides when and which tool to call. OpenAI function calling format: JSON schema definitions → model outputs structured call → execute → feed result back. Anthropic tool use. Training for tool use: ToolLLM, Gorilla. Multi-step tool use and planning. Error handling and retry strategies. Tool selection when there are hundreds of tools.
- **Hour 2 Code:** Implement a tool-use system: define tools with JSON schemas → LLM selects and calls → execute tools → feed results back. Handle multi-step tool chains. Implement error handling with retries.
- **Hour 3 Challenge:** Build a research assistant that uses tools: web search, calculator, code execution, file reader. Handle complex multi-step queries. **Interview Q:** "Design a tool-use system where the LLM has access to 500 enterprise tools (APIs, databases, internal services). How do you handle tool discovery, selection, authentication, and error recovery?"

### Day 114 — Multi-Turn Conversation & Context Management
- **Hour 1 Theory:** Multi-turn challenges: context window limits, growing latency/cost with conversation length. Context management strategies: truncation (FIFO), summarization (compress old messages), sliding window with pinned messages, retrieval-augmented conversation (retrieve relevant history). System prompt caching. Conversation state machines. Context window budgeting: system prompt + conversation history + user message + tools + generation.
- **Hour 2 Code:** Implement conversation management with: automatic summarization of old messages, retrieval over conversation history, context budget tracking, and system prompt caching. Build a chatbot with long-term memory.
- **Hour 3 Challenge:** Build a chatbot that maintains coherent 100+ turn conversations without losing context. **Interview Q:** "Your chatbot loses context after 20 turns. Users complain it 'forgets.' Design a memory architecture that handles 1000+ turn conversations efficiently."

### Day 115 — LLM Reasoning: CoT, ToT, ReAct & Process Reward Models
- **Hour 1 Theory:** Chain-of-Thought (CoT): "Let's think step by step." Few-shot CoT: provide reasoning examples. Self-consistency: sample $k$ CoT paths, majority vote. Tree of Thought (ToT): explore multiple reasoning branches with BFS/DFS + evaluation. ReAct: interleaving reasoning and action. Process Reward Models (PRM): reward each reasoning step, not just final answer. Outcome Reward Models (ORM) vs PRM trade-offs. MCTS for LLM reasoning (AlphaGo-style). Faithful reasoning vs confabulation — how to tell the difference.
- **Hour 2 Code:** Implement CoT prompting and self-consistency for GSM8K. Implement Tree of Thought with value function. Build a ReAct agent with step-by-step reasoning and tool use.
- **Hour 3 Challenge:** Build a mathematical theorem prover using ToT with step verification. **Interview Q:** "LLMs are notoriously bad at multi-step reasoning. Propose a system that achieves reliable 10-step logical reasoning. Discuss CoT, ToT, verification, and when to fall back to symbolic methods."

### Day 116 — Code Generation: HumanEval, SWE-Bench & Repository-Level
- **Hour 1 Theory:** Code LLM training: pre-train on code corpus, instruction tune for coding tasks. Fill-in-the-Middle (FIM): train model to fill missing code spans (prefix-suffix-middle format). Repository-level context: understanding imports, dependencies, API usage. Code evaluation: HumanEval (function-level), MBPP (basic problems), SWE-Bench (real GitHub issues). Test-driven development with LLMs. Code review and debugging capabilities.
- **Hour 2 Code:** Evaluate a code model on HumanEval with pass@k metric. Implement FIM prompting. Build a code completion system with repository context (file tree, imports, related functions).
- **Hour 3 Challenge:** Build a system that takes a natural language description of a function, generates code, writes tests, and iterates until tests pass. **Interview Q:** "Design the architecture for a Copilot-like code assistant. Cover: IDE integration, context selection, model serving, personalization, and evaluation. How do you measure if it actually makes developers more productive?"

### Day 117 — Multi-Modal LLMs: Architecture & Training
- **Hour 1 Theory:** Multi-modal LLM architectures: Vision encoder (CLIP/SigLIP ViT) → Projector (MLP/perceiver/Q-former) → Language model. LLaVA training stages: (1) Feature alignment: freeze vision+LLM, train projector on image-caption pairs. (2) Visual instruction tuning: unfreeze LLM, train on visual QA/conversation data. Resolution handling: dynamic resolution, multi-crop. Video understanding: frame sampling, temporal reasoning. Audio-language models: Whisper encoder → LLM.
- **Hour 2 Code:** Run inference with LLaVA on image+text inputs. Fine-tune a multi-modal model using LoRA. Implement a simple multi-image comparison system.
- **Hour 3 Challenge:** Build a document understanding system that can answer questions about screenshots, charts, and diagrams. **Interview Q:** "Design a multi-modal AI system for an insurance company that processes claims: photos of damage, receipts, medical reports. Cover: OCR, visual understanding, document extraction, and reasoning."

### Day 118 — Small Language Models: Phi, Gemma, On-Device LLMs
- **Hour 1 Theory:** Small model philosophy: data quality > model size. Phi series: "textbook-quality" synthetic data. Gemma-2B: knowledge distillation from larger models. SmolLM, TinyLlama. Pruning large models to create small ones. On-device deployment: model size limits (RAM, storage), latency requirements, battery considerations. Quantization for mobile: INT4, mixed precision. Frameworks: ONNX Runtime Mobile, TensorFlow Lite, Core ML, ExecuTorch, MLC-LLM.
- **Hour 2 Code:** Run a small model (Phi-3-mini or Gemma-2B) locally. Quantize to GGUF and run with llama.cpp. Benchmark: model size, inference speed, and quality trade-offs across quantization levels.
- **Hour 3 Challenge:** Deploy a quantized small model on your local machine and build a chat interface that runs entirely offline. **Interview Q:** "Your company wants to run an LLM on smartphones (iPhone 15, Galaxy S24). What's the maximum model size, and how do you achieve acceptable quality and latency? Discuss the full optimization stack."

### Day 119 — LLM Security: Prompt Injection, Data Extraction & Adversarial Attacks
- **Hour 1 Theory:** Direct prompt injection: user overrides system prompt. Indirect prompt injection: malicious content in retrieved documents. Data extraction attacks: "repeat everything above." Membership inference: determine if specific data was in training set. Model stealing: extract model weights through API queries. PII extraction from memorized training data. Defense strategies: input sanitization, output filtering, instruction hierarchy, sandbox execution. Prompt injection detection models.
- **Hour 2 Code:** Implement a defense-in-depth system: input scanner → instruction hierarchy enforcement → output filter → PII detector. Test against a suite of prompt injection attacks. Implement a prompt injection detection classifier.
- **Hour 3 Challenge:** Red-team your own system: try to break through the defenses you built. Fix vulnerabilities. **Interview Q:** "Your LLM-powered customer service bot is deployed to 1M users. An attacker discovers it can be tricked into revealing other customers' information. Describe your incident response, technical fix, and prevention strategy."

### Day 120 — Phase 4 Capstone: Fine-Tune & Deploy a Custom LLM
- **Hour 1 Theory:** End-to-end review of the LLM lifecycle. Decision framework: when to prompt vs fine-tune vs pre-train. Cost analysis for each approach. Complete quality assurance pipeline: automated benchmarks → LLM-as-judge → human evaluation → A/B testing in production.
- **Hour 2 Code:** Build the complete pipeline: (1) Curate instruction data (synthetic + manual), (2) QLoRA fine-tune a 7B model, (3) DPO alignment using preference data, (4) Evaluate on benchmarks + MT-Bench + custom evaluation, (5) Merge and quantize for deployment, (6) Serve with OpenAI-compatible API.
- **Hour 3 Challenge:** Do it all from memory with a different base model and domain. **Interview Q:** "You're the ML platform lead tasked with building an internal fine-tuning platform for your 500-person company. Non-ML engineers should be able to fine-tune models for their use cases. Design the platform: UI, APIs, compute management, evaluation, and deployment."

---

# ═══════════════════════════════════════════════════════════════
# PHASE 5: AGENTIC AI, MCP & TOOL-USE SYSTEMS
# Days 121–150 | "Building Autonomous AI Systems"
# ═══════════════════════════════════════════════════════════════

> **Phase Objective:** Master the emerging paradigm of AI agents — systems that can reason, plan, use tools, and take actions. Build production-grade agent systems using LangGraph, CrewAI, and MCP.

### Phase 5 Milestone Checklist
- [ ] Can build a ReAct agent from scratch with raw API calls
- [ ] Can design complex agent workflows using LangGraph
- [ ] Can build and deploy MCP servers with FastMCP
- [ ] Can orchestrate multi-agent systems with CrewAI
- [ ] Can implement human-in-the-loop approval gates
- [ ] Can evaluate agent systems with trajectory analysis and task completion metrics

---

## Week 17–18: Agent Foundations (Days 121–130)

### Day 121 — Agent Architecture: Perception-Reasoning-Action Loop
- **Hour 1 Theory:** Cognitive architecture for AI agents. Observe → Think → Act → Reflect cycle. ReAct framework formalization: Thought → Action → Observation → ... Agent vs chain vs pipeline (deterministic vs autonomous). State machines for agent behavior. Agent design patterns: router, planner, executor, critic. When agents are appropriate (and when they're over-engineering). Token cost analysis for agent loops.
- **Hour 2 Code:** Build a simple ReAct agent from scratch using raw OpenAI/Anthropic API calls. Implement the thought-action-observation loop with tool execution. Add structured output for action parsing.
- **Hour 3 Challenge:** Extend your agent to handle multi-step mathematical reasoning with tool use (calculator, Python code execution). **Interview Q:** "You're designing an agent system for customer support that handles 10K concurrent conversations. Discuss architecture, state management, error recovery, and cost optimization."

### Day 122 — LangChain Foundations: Chains, Prompts & Memory
- **Hour 1 Theory:** LangChain architecture: models (LLMs, chat models, embeddings), prompts (templates, selectors), chains (sequential, parallel), memory (buffer, summary, vector store), output parsers. LCEL (LangChain Expression Language): pipe operator, Runnables, RunnableParallel, RunnablePassthrough. Callbacks for logging and streaming.
- **Hour 2 Code:** Build a conversational QA system with LangChain. Implement custom chains with LCEL. Add conversation memory with summarization. Implement streaming output.
- **Hour 3 Challenge:** Build a research assistant chain: take a question → search web → summarize results → answer with citations. **Interview Q:** "LangChain has been criticized for excessive abstraction. When is it the right choice vs raw API calls? Discuss engineering trade-offs."

### Day 123 — LangGraph: Stateful Multi-Actor Agent Graphs
- **Hour 1 Theory:** LangGraph as a state machine framework for agentic applications. Core concepts: graph = nodes + edges + state. `StateGraph` with typed state (TypedDict or Pydantic). Conditional edges for branching logic. Entry points and finish conditions. Persistence layer (checkpointing). Human-in-the-loop: interrupt, review, approve/reject. Time-travel debugging: replay from any checkpoint.
- **Hour 2 Code:** Build a research agent using LangGraph with: web search node → content analysis node → decision node (conditional edge: need more info? → search again, or summarize) → output node. Add persistence with SQLite checkpointer.
- **Hour 3 Challenge:** Build a code review agent that reads code, identifies issues, suggests fixes, and iterates until quality threshold is met. **Interview Q:** "Design a multi-agent code generation system that writes, tests, and deploys code with human approval gates. Discuss the state graph and failure modes."

### Day 124 — LangGraph Advanced: Sub-Graphs, Streaming & Persistence
- **Hour 1 Theory:** Nested sub-graphs for modular, reusable agent components. Map-reduce patterns for parallel processing. Streaming modes: stream values (full state), stream updates (deltas), stream events (all intermediate steps). Breakpoints for human-in-the-loop. Long-running agents with PostgreSQL persistence. Time-travel debugging: step back, modify state, replay. Command pattern for dynamic graph modification.
- **Hour 2 Code:** Build a multi-step research assistant with sub-graphs for different research domains (web, academic, code). Implement streaming output with intermediate status updates. Add PostgreSQL persistence for long-running tasks.
- **Hour 3 Challenge:** Build a data analysis agent: upload CSV → LangGraph orchestrates analysis (statistics, visualization, insights) → produces report. **Interview Q:** "Your LangGraph agent costs $2 per query due to multiple LLM calls. The budget is $0.10/query. Redesign the system to hit the budget target without sacrificing quality."

### Day 125 — Model Context Protocol (MCP): Architecture & Specification
- **Hour 1 Theory:** MCP specification: client-server architecture for standardized tool integration. Protocol stack: transport (stdio, SSE, Streamable HTTP) → JSON-RPC 2.0 → MCP primitives. Three primitive types: Resources (data the server exposes, like files), Tools (functions the server offers), Prompts (reusable prompt templates). Capability negotiation: client and server declare what they support. Lifecycle: initialize → operate → shutdown. Sampling: server can request LLM completions from the client. Why MCP matters: standardization enables ecosystem effects (write once, use everywhere).
- **Hour 2 Code:** Build a FastMCP server that exposes: a calculator tool, a file reader resource, a weather API tool, and a code analysis prompt. Connect to Claude Desktop and test.
- **Hour 3 Challenge:** Build an MCP server that provides database query capabilities with schema introspection and query validation. **Interview Q:** "MCP standardizes tool use for LLMs. Compare this to function calling in OpenAI's API. Discuss protocol design trade-offs, security implications, and ecosystem effects."

### Day 126 — FastMCP Server Development: Tools, Resources & Prompts
- **Hour 1 Theory:** FastMCP Python SDK deep dive. `@mcp.tool()` decorator: automatic schema generation from type hints and docstrings. `@mcp.resource()`: URI-based data access (file://, db://, api://). `@mcp.prompt()`: parameterized prompt templates. Pydantic models for input validation. Error handling: raise `McpError` with structured error codes. Context object: access logging, request metadata. Testing MCP servers: `mcp dev` for interactive testing, unit tests with `mcp.testing`.
- **Hour 2 Code:** Build a production MCP server for a data analytics platform: SQL query tool (with injection prevention), chart generation tool (matplotlib → base64), data export tool (CSV/JSON), dataset listing resource, and analysis prompt template. Add comprehensive error handling and logging.
- **Hour 3 Challenge:** Build an MCP server that wraps a REST API (e.g., GitHub API) with proper authentication, rate limiting, and caching. **Interview Q:** "You're building an MCP server ecosystem for a Fortune 500 company. 50 internal services need to be exposed as MCP tools. Design the architecture: server registry, authentication, rate limiting, monitoring, and versioning."

### Day 127 — MCP Advanced: Transport, Security, Composition & Sampling
- **Hour 1 Theory:** Transport deep dive: stdio (local, subprocess), SSE (HTTP-based, older), Streamable HTTP (latest standard, supports both request-response and streaming). Authentication: OAuth2 flows for MCP, API key management. Authorization: per-tool permissions, user-scoped access. Server composition: chaining MCP servers (output of one → input of another). MCP proxy pattern: aggregate multiple servers behind one. Sampling: server requests LLM completion from client (reverse tool use). Root listing: exposing filesystem boundaries.
- **Hour 2 Code:** Build an MCP server with Streamable HTTP transport. Implement OAuth2 authentication. Build an MCP proxy that aggregates three specialized servers. Implement sampling (server-initiated LLM calls).
- **Hour 3 Challenge:** Build a secure MCP server that enforces per-user tool access control and logs all operations for audit. **Interview Q:** "An MCP server has access to your production database. How do you prevent: SQL injection through LLM-generated queries, unauthorized data access, and accidental data modification? Design the complete security model."

### Day 128 — CrewAI: Multi-Agent Orchestration
- **Hour 1 Theory:** CrewAI concepts: Agents (role, goal, backstory, tools, LLM), Tasks (description, expected output, dependencies, context), Crews (collection of agents + tasks), Processes (sequential, hierarchical, consensual). Sequential: agents execute tasks in order. Hierarchical: manager agent delegates. Agent delegation: agents can delegate sub-tasks. Memory: short-term (within crew execution), long-term (across executions), entity memory (knowledge about entities).
- **Hour 2 Code:** Build a content creation crew: researcher agent (with web search tool), writer agent, editor agent (with quality criteria). Define tasks with dependencies. Run the crew and analyze the output chain.
- **Hour 3 Challenge:** Build an investment analysis crew: data collector agent, financial analyst agent, risk assessor agent, report writer agent. Run on real stock data. **Interview Q:** "Compare LangGraph and CrewAI for building production agent systems. When would you choose one over the other? Discuss debugging, observability, and scaling."

### Day 129 — CrewAI Advanced: Custom Tools, Memory & Integration
- **Hour 1 Theory:** Custom tool creation: `@tool` decorator, BaseTool class, structured inputs with Pydantic. CrewAI + MCP integration: using MCP servers as CrewAI tools. Long-term memory: RAG-based knowledge retention across crew executions. Output validation: Pydantic models for structured task outputs. Guardrails: output validators, maximum iterations, error handling. Callbacks for monitoring. CrewAI Flows: orchestrate multiple crews in complex workflows.
- **Hour 2 Code:** Build a CrewAI system with custom tools that connect to MCP servers. Implement long-term memory using a vector store. Add output validation with Pydantic models. Build a multi-crew flow.
- **Hour 3 Challenge:** Build a customer onboarding system with multiple crews: research crew (verify company info), compliance crew (check regulations), setup crew (configure accounts). **Interview Q:** "A crew of 5 agents costs $5 per task execution and takes 3 minutes. You need to process 10,000 tasks per day. Design the scaling strategy and optimize for cost and throughput."

### Day 130 — Agent Evaluation & Testing
- **Hour 1 Theory:** Agent evaluation dimensions: task completion rate, tool call accuracy, reasoning quality, cost efficiency, latency. Trajectory analysis: was each step necessary? Were there loops? Benchmarks: AgentBench, SWE-bench, GAIA (General AI Assistants), WebArena. Testing pyramid for agents: unit tests (individual tools) → integration tests (agent-tool interaction) → end-to-end tests (full task completion) → adversarial tests (edge cases, failures). Mock LLMs for deterministic testing. Regression testing for prompt changes.
- **Hour 2 Code:** Build a comprehensive test suite: unit tests for each tool, integration tests with mock LLM responses, end-to-end tests with real LLM. Implement trajectory evaluation: step count, cost, accuracy. Build regression test fixtures.
- **Hour 3 Challenge:** Create a benchmark suite of 50 tasks for your agent system. Measure performance across multiple LLM backends. **Interview Q:** "Your agent system works 95% of the time in testing but fails unpredictably in production. Design a reliability engineering strategy: testing, monitoring, fallbacks, and continuous improvement."

---

## Days 131–140: Advanced Agent Patterns

### Day 131 — Planning Agents: Plan-and-Execute & LLMCompiler
- **Hour 1 Theory:** Plan-and-Execute pattern: separate planning (create step-by-step plan) from execution (execute each step). Re-planning: revise plan based on intermediate results. LLMCompiler: parallel function calling — identify independent steps and execute concurrently. Task DAG generation. Planning with constraints (budget, time, available tools). Comparison: ReAct (interleaved) vs Plan-and-Execute (separated).
- **Hour 2 Code:** Implement Plan-and-Execute agent in LangGraph: planner node → executor nodes → re-planner. Implement LLMCompiler pattern for parallel tool calls. Compare latency with sequential ReAct.
- **Hour 3 Challenge:** Build a trip planning agent that creates a full itinerary (flights, hotels, activities) using parallel API calls. **Interview Q:** "Your agent needs to complete complex 20-step tasks. ReAct fails because it loses context. Plan-and-Execute fails because the plan becomes stale. Design a hybrid approach."

### Day 132 — Reflection & Self-Critique Agents (Reflexion)
- **Hour 1 Theory:** Reflexion: agent attempts task → evaluates output → generates verbal reflection → retries with reflection in context. Self-critique patterns: rubric-based evaluation, LLM-as-judge, unit test verification. LATS (Language Agent Tree Search): combine reflection with tree search over actions. Generator-Critic architecture. Iterative refinement vs single-pass generation.
- **Hour 2 Code:** Implement Reflexion agent in LangGraph: attempt → evaluate → reflect → retry (with max iterations). Build a self-critiquing code agent that writes code, runs tests, reflects on failures, and fixes bugs.
- **Hour 3 Challenge:** Build a writing agent that drafts, self-critiques against a rubric, and refines until quality threshold is met. **Interview Q:** "Reflection agents improve quality but multiply cost by 3-5x. Design a system that uses reflection only when needed (adaptive reflection). How do you predict when reflection will be beneficial?"

### Day 133 — Multi-Agent Debate, Consensus & Collaboration
- **Hour 1 Theory:** Multi-agent debate: multiple agents argue different perspectives, converge on answer. Improves factuality and reduces hallucination. Society of Mind: specialized agents contribute expertise. Consensus algorithms: majority voting, weighted voting (by confidence), arbitrator agent. Collaboration patterns: peer-to-peer, hub-and-spoke, hierarchical. Agent communication protocols: shared blackboard, message passing, structured channels.
- **Hour 2 Code:** Implement a debate system: two agents argue, judge agent evaluates and declares winner. Build a collaborative coding system: architect agent designs, developer agent implements, reviewer agent critiques.
- **Hour 3 Challenge:** Build a fact-checking system using multi-agent debate: claim → multiple research agents investigate → debate evidence → consensus on verdict. **Interview Q:** "Multi-agent debate improves accuracy but is slow and expensive. Design a system that uses debate for high-stakes decisions and fast single-agent processing for routine ones."

### Day 134 — Agent Tool Creation: Agents that Build Their Own Tools
- **Hour 1 Theory:** LATM (LLM-As-Tool-Maker): agent identifies need for tool → writes tool code → tests tool → adds to toolkit → uses in future. Code generation as tool creation. Tool caching and reuse. Safety: sandboxing generated tool code. Verification: unit tests for generated tools. Tool evolution: improving tools based on usage feedback.
- **Hour 2 Code:** Build an agent that can create Python tools: takes natural language description → generates code → tests → registers as callable tool. Implement sandboxed execution. Build a tool library with versioning.
- **Hour 3 Challenge:** Give an agent a task that requires a tool that doesn't exist. Verify it creates the tool, uses it, and caches it for future use. **Interview Q:** "An agent that creates its own tools is powerful but dangerous. Design the safety model: sandboxing, code review, testing, and approval workflows. What types of tools should never be auto-generated?"

### Day 135 — Code Agents: AI-Powered Software Development (SWE-Agent)
- **Hour 1 Theory:** SWE-Agent architecture: LLM interacts with a computer interface (terminal, editor, browser). Action space: edit file, run command, search codebase, navigate. Agent-Computer Interface (ACI) design: what makes a good interface for an LLM? Repository understanding: file tree, dependency graph, test suite. SWE-Bench: real GitHub issues as benchmarks. Aider: conversational coding with git integration. OpenHands/Devin architecture.
- **Hour 2 Code:** Build a simplified code agent that can: read files, edit files, run tests, search code (grep/tree). Use LangGraph for the interaction loop. Test on a simple bug-fixing task.
- **Hour 3 Challenge:** Build a code agent that can solve simple GitHub issues: read issue → understand codebase → write fix → run tests → create PR description. **Interview Q:** "Design the architecture for an AI coding assistant that works on repositories with 1M+ lines of code. How does it build context, make changes safely, and validate its work?"

### Day 136 — Browser Agents: Web Automation with AI
- **Hour 1 Theory:** Browser agents: LLM controls a web browser. Observation space: DOM, screenshots, accessibility tree. Action space: click, type, scroll, navigate, extract. Challenges: dynamic pages, anti-bot measures, complex UIs. Browser automation: Playwright, Selenium. Multi-modal agents: use screenshots for visual understanding. WebArena benchmark. Set-of-marks prompting: overlay numbered labels on interactive elements.
- **Hour 2 Code:** Build a browser agent using Playwright + LLM: navigate to a website, fill forms, extract information. Implement screenshot-based and DOM-based observation modes.
- **Hour 3 Challenge:** Build an agent that can compare prices across 3 e-commerce sites for a given product. **Interview Q:** "Design a browser agent system for automated software testing. It should navigate your web app, test user flows, and report bugs. Discuss reliability, parallelism, and handling dynamic content."

### Day 137 — Workflow Automation: Enterprise Integration Patterns
- **Hour 1 Theory:** Enterprise integration: connecting agents to real business systems. API integration patterns: REST, GraphQL, webhooks, message queues. Data pipeline triggers: agent initiates ETL processes. CRM/ERP integration (Salesforce, SAP). Email automation. Calendar management. Document generation (PDF, DOCX). Workflow engines: Temporal, n8n, Zapier. Agent-triggered vs event-triggered workflows.
- **Hour 2 Code:** Build an agent-powered workflow: receive customer email → extract intent and entities → query CRM → generate response → create ticket → send reply. Use LangGraph for orchestration.
- **Hour 3 Challenge:** Build a hiring workflow agent: receive resume → extract info → match to job requirements → schedule interview → send notification. **Interview Q:** "Design an AI-powered operations platform that automates 80% of IT support tickets. Cover: ticket classification, automated resolution, escalation, and human handoff."

### Day 138 — Human-in-the-Loop: Approval Gates, Escalation & Feedback
- **Hour 1 Theory:** Why HITL matters: high-stakes decisions, regulatory requirements, building trust. Approval gate patterns: interrupt before critical actions, present plan for review, require explicit approval. Escalation: agent detects uncertainty → escalates to human. Confidence-based routing: high confidence → auto-execute, low confidence → human review. Feedback loops: human corrections improve agent over time. Active learning for agents.
- **Hour 2 Code:** Implement HITL in LangGraph: interrupt at critical nodes → present action plan → wait for approval → execute or modify. Build an escalation system based on agent confidence. Implement feedback collection and storage.
- **Hour 3 Challenge:** Build a financial transaction agent that requires human approval for transactions over $1000 and auto-processes smaller ones. **Interview Q:** "Your agent system processes insurance claims. Regulators require human review of all denials. Design the HITL system: approval workflow, SLAs, auditing, and the feedback loop for continuous improvement."

### Day 139 — Agent Observability: Tracing, Logging & Debugging
- **Hour 1 Theory:** Observability for agent systems: tracing (full execution trace), logging (structured logs), metrics (latency, cost, success rate). LangSmith: LangChain's observability platform (traces, datasets, evaluations). Arize Phoenix: open-source traces and evaluations. OpenTelemetry for agents. Trace format: spans with parent-child relationships. Key metrics: tokens used, cost per run, step count, tool call success rate, error rate. Debugging strategies: replay from trace, step-through execution.
- **Hour 2 Code:** Integrate LangSmith tracing into your LangGraph agent. Build a custom metrics dashboard with: cost per query, success rate, average steps, error distribution. Implement trace-based debugging (replay failed runs).
- **Hour 3 Challenge:** Build an alerting system that detects: agent loops (>10 steps), excessive cost (>$1 per query), repeated failures, and unusual tool usage patterns. **Interview Q:** "Your agent system processes 50K requests/day. 2% fail silently (produce wrong answers without errors). Design the observability stack to detect and diagnose these silent failures."

### Day 140 — Agent Cost Optimization
- **Hour 1 Theory:** Agent cost anatomy: LLM calls (major cost), tool executions, infrastructure. Cost reduction strategies: model routing (cheap model for easy tasks, expensive for hard), caching (semantic cache for repeated queries), prompt compression (LLMLingua), shorter system prompts, fewer agent steps (better planning), batch processing, response streaming for early termination. Token-aware budgeting: set maximum tokens per agent run.
- **Hour 2 Code:** Implement a cost-aware agent: token budget tracking, model routing (GPT-3.5 for simple tasks, GPT-4 for complex), semantic caching, and early termination when budget is exhausted. Measure cost savings.
- **Hour 3 Challenge:** Reduce your agent system's cost by 80% while maintaining 95% of quality. Document every optimization. **Interview Q:** "Your agent platform costs $500K/month serving 1M queries. The CFO wants it under $100K. Design the optimization roadmap: model routing, caching, prompt engineering, and fine-tuning. Prioritize by impact."

---

## Days 141–150: Complex Agent Systems

### Day 141 — RAG Agents: Adaptive Retrieval & Corrective RAG
- **Hour 1 Theory:** RAG Agent patterns: (1) Adaptive retrieval: agent decides when to retrieve vs use parametric knowledge. (2) Corrective RAG (CRAG): retrieve → grade documents → if irrelevant, try web search → generate. (3) Self-RAG: model generates special tokens [Retrieve], [IsRel], [IsSup], [IsUse] to self-regulate retrieval. (4) Agentic RAG: full agent loop for complex multi-source queries. Query routing: direct to the right knowledge source based on query type.
- **Hour 2 Code:** Build a CRAG agent in LangGraph: query → retrieve → grade relevance → (if poor) → web search → generate. Implement adaptive retrieval with the agent deciding when retrieval is needed.
- **Hour 3 Challenge:** Build a multi-source RAG agent that can query: local documents, web search, SQL database, and API endpoints, dynamically choosing the best source. **Interview Q:** "Design a RAG agent for a hospital that needs to query: patient records (SQL), clinical guidelines (documents), drug interactions (API), and research papers (search). Discuss routing, access control, and citation."

### Day 142 — Multi-Modal Agents: Vision + Code + Web
- **Hour 1 Theory:** Multi-modal agent capabilities: visual understanding (screenshots, images), code execution, web browsing, file manipulation. Architecture: multi-modal LLM as brain + specialized tools for each modality. Challenges: grounding visual information in actions, handling complex UIs, managing multiple modality contexts simultaneously. Use cases: data analysis from charts, UI testing, document processing.
- **Hour 2 Code:** Build a multi-modal agent that can: take screenshots, analyze images, execute Python code, browse the web, and read/write files. Use GPT-4V or Claude for visual understanding.
- **Hour 3 Challenge:** Build an agent that analyzes a business dashboard screenshot, extracts data, creates a Python analysis, and generates a written report with charts. **Interview Q:** "Design a document processing agent that handles PDFs with mixed content: text, tables, charts, handwritten notes. It must extract structured data with 99% accuracy. Discuss the architecture and fallback strategies."

### Day 143 — Agent Memory Systems: Short-Term, Long-Term & Episodic
- **Hour 1 Theory:** Memory taxonomy for agents: Working memory (current context window). Short-term memory (within session, conversation buffer). Long-term memory (persistent across sessions, vector store + metadata). Episodic memory (specific past interactions, similar to case-based reasoning). Semantic memory (general knowledge, embeddings). Procedural memory (learned workflows). Memory retrieval: recency, relevance, importance scoring. Memory consolidation: summarize and compress old memories. MemGPT architecture.
- **Hour 2 Code:** Implement a comprehensive memory system: vector store for long-term memory, conversation buffer for short-term, episodic store with recency-weighted retrieval. Build a chatbot that remembers user preferences across sessions.
- **Hour 3 Challenge:** Build an agent that learns user preferences over time and personalizes its responses based on accumulated memory. **Interview Q:** "Design a memory system for a personal AI assistant used by 10M users. Each user has years of conversation history. Discuss storage, retrieval, privacy, and the cold-start problem."

### Day 144 — Agent Communication: Protocols, Message Passing & A2A
- **Hour 1 Theory:** Agent-to-agent communication patterns: direct messaging, broadcast, publish-subscribe, shared state (blackboard). Google's Agent-to-Agent (A2A) protocol: standardized agent interoperability. Message format: sender, recipient, content, type (request/response/notification), context. Coordination patterns: pipeline, scatter-gather, choreography, orchestration. Conflict resolution when agents disagree. Communication overhead and optimization.
- **Hour 2 Code:** Implement a multi-agent system with structured communication: message queue, agent registry, and routing. Build a scatter-gather pattern: coordinator sends task to multiple specialist agents, aggregates results.
- **Hour 3 Challenge:** Build a negotiation system: buyer agent and seller agent negotiate a price through structured messages until agreement or impasse. **Interview Q:** "You're building a platform where third-party agents can interact with your company's agents. Design the communication protocol, trust model, and security boundaries."

### Day 145 — Building MCP Ecosystems: Server Discovery, Registry & Composition
- **Hour 1 Theory:** MCP ecosystem architecture: multiple specialized servers working together. Server registry and discovery: how clients find available MCP servers. Server composition patterns: gateway server that routes to specialized servers, pipeline composition (output of one → input of another). MCP marketplace: publishing and consuming community servers. Versioning and compatibility: handling server updates without breaking clients. Configuration management for multi-server setups.
- **Hour 2 Code:** Build an MCP ecosystem with 3 specialized servers (data analysis, document processing, web search) + 1 gateway server that routes requests. Implement server health checks and failover.
- **Hour 3 Challenge:** Build a composable MCP system where servers can be dynamically added/removed without restarting the client. **Interview Q:** "Design an MCP server marketplace for enterprise: server publishing, versioning, security review, access control, usage metering, and billing. How do you ensure server quality and security?"

### Day 146 — Agent Security: Sandboxing, Permissions & Trust Boundaries
- **Hour 1 Theory:** Agent security threat model: tool misuse, privilege escalation, data exfiltration, resource abuse, prompt injection through tools. Defense layers: principle of least privilege (agents only get needed permissions), sandboxed execution (Docker containers, gVisor), rate limiting, budget caps, audit logging. Trust boundaries: LLM output is untrusted input to tools. Tool authorization: user-scoped permissions. Secure coding for agent tools: input validation, output sanitization.
- **Hour 2 Code:** Implement a secure agent execution environment: Docker-based sandbox for code execution, permission model for tool access, rate limiter, budget tracker, and comprehensive audit logging.
- **Hour 3 Challenge:** Build a penetration testing suite for your agent system: try to escape sandbox, access unauthorized data, exceed budget, and exfiltrate information. **Interview Q:** "Your agent has access to production databases, internal APIs, and can execute code. An attacker sends a crafted message that makes the agent drop all tables. Design the security architecture to prevent this."

### Day 147 — Scaling Agents: Concurrent Execution, Queuing & Rate Limiting
- **Hour 1 Theory:** Scaling challenges: LLM API rate limits, tool execution bottlenecks, state management for concurrent agents. Concurrency patterns: asyncio for I/O-bound operations, thread/process pools for CPU-bound. Queue-based architecture: request queue → worker pool → result queue. Rate limiting: token bucket, sliding window. Backpressure: slow down intake when processing is saturated. Horizontal scaling: stateless agents with external state store.
- **Hour 2 Code:** Build a scalable agent service: FastAPI endpoint → Redis queue → async worker pool → result streaming. Implement rate limiting per user and per API. Handle 100 concurrent agent sessions.
- **Hour 3 Challenge:** Load test your agent system: simulate 500 concurrent users, identify bottlenecks, and optimize to handle the load. **Interview Q:** "Your agent platform needs to handle 100K requests per hour with a p99 latency of 30 seconds. Design the scaling architecture including queuing, worker management, and auto-scaling."

### Day 148 — Production Agent Deployment: Containerization & Orchestration
- **Hour 1 Theory:** Deployment patterns for agents: containerization with Docker, orchestration with Kubernetes. Agent as a microservice: stateless compute + external state store. Deployment strategies: blue-green, canary, rolling update. Configuration management: environment variables, secrets, feature flags. Health checks: liveness (is the agent running?), readiness (can it handle requests?). Graceful shutdown: complete in-flight requests before stopping.
- **Hour 2 Code:** Containerize your agent system with Docker (multi-stage build). Create Kubernetes deployment manifests: Deployment, Service, ConfigMap, Secret, HPA (autoscaler). Implement health check endpoints and graceful shutdown.
- **Hour 3 Challenge:** Deploy your agent system to a local Kubernetes cluster (minikube/kind). Implement canary deployment: route 10% of traffic to new version. **Interview Q:** "Your agent platform serves 50 enterprise customers, each with custom tools and configurations. Design the multi-tenant deployment architecture: isolation, resource allocation, and cost attribution."

### Day 149 — Agent Failure Recovery & Graceful Degradation
- **Hour 1 Theory:** Failure modes: LLM API timeout/error, tool execution failure, context length overflow, infinite loops, partial completion. Recovery strategies: retry with exponential backoff, fallback to simpler model, checkpoint and resume, partial result delivery. Circuit breaker pattern: stop calling a failing service. Graceful degradation: if RAG fails → use parametric knowledge, if planning fails → use ReAct, if tool fails → skip and inform user. Dead letter queue for unrecoverable failures.
- **Hour 2 Code:** Implement comprehensive error handling: retry with backoff, circuit breaker for external APIs, checkpoint/resume for long-running agents, fallback chains (GPT-4 → GPT-3.5 → cached response). Implement dead letter queue for failed requests.
- **Hour 3 Challenge:** Simulate various failures (API timeouts, tool crashes, budget exhaustion) and verify your system handles each gracefully. **Interview Q:** "Your production agent system had a 2-hour outage because the LLM API rate limit was hit. Design the resilience architecture: multi-provider failover, local model fallback, queue management, and degradation policies."

### Day 150 — Phase 5 Capstone: Build a Production Multi-Agent System
- **Hour 1 Theory:** Architecture review: bringing all Phase 5 concepts together. Reference architecture for production agent systems: API gateway → request router → agent orchestrator (LangGraph) → agent pool (CrewAI crews) → tool layer (MCP servers) → state store (Redis/PostgreSQL) → observability (LangSmith/Phoenix) → evaluation pipeline.
- **Hour 2 Code:** Build the complete system: (1) FastAPI gateway with authentication, (2) LangGraph orchestrator with adaptive retrieval, (3) CrewAI crew for complex multi-step tasks, (4) 3 MCP tool servers (data, search, code execution), (5) Human-in-the-loop approval for sensitive actions, (6) LangSmith observability, (7) Error recovery and fallback chains, (8) Cost tracking dashboard.
- **Hour 3 Challenge:** Deploy, load test, break, fix, and document the entire system. **Interview Q:** "You're the founding AI engineer at a startup building an 'AI chief of staff' for executives. Design the complete system: agent architecture, tool ecosystem, memory, security, deployment, and go-to-market strategy."

---

# ═══════════════════════════════════════════════════════════════
# PHASE 6: PRODUCTION LLMOps & SYSTEM DESIGN
# Days 151–180 | "Ship It to Production"
# ═══════════════════════════════════════════════════════════════

> **Phase Objective:** Master the engineering required to deploy, serve, monitor, and maintain LLM-powered systems at scale. This is what separates ML engineers from ML researchers. You will also prepare for MAANG-level system design interviews.

### Phase 6 Milestone Checklist
- [ ] Can deploy and benchmark an LLM with vLLM
- [ ] Can design a complete LLM serving architecture for 10K+ concurrent users
- [ ] Can implement CI/CD for ML models with automated testing
- [ ] Can design monitoring and alerting for LLM quality degradation
- [ ] Can whiteboard 5 different ML system designs at MAANG interview level
- [ ] Have a portfolio of 3+ production-ready projects

---

## Week 21–22: LLM Serving & Infrastructure (Days 151–160)

### Day 151 — LLM Serving Fundamentals: vLLM, TGI, TensorRT-LLM
- **Hour 1 Theory:** Serving challenges: memory-bound (KV-cache), compute-bound (prefill vs decode). Static batching vs continuous batching (dynamic batching during generation). PagedAttention (vLLM): virtual memory for KV-cache, reducing fragmentation from 60-80% waste to <4%. TGI: HuggingFace serving stack. TensorRT-LLM: NVIDIA optimized runtime with FP8 support. SGLang: fast serving with RadixAttention. Key metrics: Time-to-First-Token (TTFT), Time-per-Output-Token (TPOT), throughput (tokens/s), requests/s.
- **Hour 2 Code:** Deploy a 7B model with vLLM. Benchmark TTFT, TPOT, throughput at various concurrency levels. Configure continuous batching, PagedAttention, and quantized inference. Compare with HuggingFace `pipeline`.
- **Hour 3 Challenge:** Build a load testing harness and find the optimal serving configuration for your hardware. Create a performance report. **Interview Q:** "You need to serve a 70B parameter model with <200ms TTFT and 10K concurrent users. Design the complete serving architecture including hardware, software, and scaling strategy."

### Day 152 — Inference Optimization: KV-Cache, Prefix Caching & Quantized Serving
- **Hour 1 Theory:** KV-cache memory: $2 \times L \times n \times d \times \text{bytes\_per\_element}$ per request. With $L=32, n=4096, d=4096, \text{FP16}$: ~4GB per request. Prefix caching: share KV-cache for common system prompts (saves recomputation). Speculative decoding in serving. Quantized inference: GPTQ (3-4 bit), AWQ (activation-aware), GGUF (CPU-friendly), FP8. KV-cache quantization (FP8 KV). Flash Attention for serving: reduces memory and improves throughput. Chunked prefill: interleave prefill and decode for better GPU utilization.
- **Hour 2 Code:** Enable prefix caching in vLLM for a shared system prompt. Benchmark memory savings. Deploy with GPTQ quantization and compare quality/speed. Implement a prompt template that maximizes prefix cache hits.
- **Hour 3 Challenge:** Serve a 13B model on a single 24GB GPU by combining quantization + prefix caching. **Interview Q:** "You're serving 100 customers, each with a 2000-token system prompt. Calculate the memory savings from prefix caching. Design the cache management strategy: eviction, invalidation, and sharing across requests."

### Day 153 — API Design for LLM Services
- **Hour 1 Theory:** OpenAI-compatible API specification: `/chat/completions`, `/embeddings`, `/models`. Request format: messages array, temperature, max_tokens, stop sequences, stream flag. Streaming with Server-Sent Events (SSE): `data: {"choices": [{"delta": {"content": "..."}}]}`. REST vs gRPC vs WebSocket for different use cases. Rate limiting strategies: per-user, per-organization, token-based. Authentication: API keys, OAuth2, JWT. Usage tracking and billing. API versioning for model updates.
- **Hour 2 Code:** Build an OpenAI-compatible API server using FastAPI: `/chat/completions` with streaming SSE, `/embeddings`, `/models`. Add rate limiting (token bucket), API key authentication, usage tracking (tokens consumed per key), and request/response logging.
- **Hour 3 Challenge:** Build a multi-model API gateway that routes requests to different backends (vLLM, Ollama, OpenAI) based on model name, with fallback. **Interview Q:** "Design the API layer for a multi-tenant LLM platform. 500 teams, each with different rate limits, model access, and billing. Cover: authentication, rate limiting, cost attribution, and SLA management."

### Day 154 — GPU Cluster Management: Multi-GPU & Multi-Node Serving
- **Hour 1 Theory:** Tensor parallelism for serving: split model layers across GPUs (NCCL communication). Pipeline parallelism: split model stages across GPUs (increases latency, increases throughput). When to use each. GPU memory optimization: KV-cache quantization (INT8/FP8), weight quantization, memory pools. CUDA graphs: capture and replay kernel sequences to reduce launch overhead. Multi-node serving: InfiniBand networking, RDMA. Disaggregated serving: separate prefill and decode onto different GPU types.
- **Hour 2 Code:** Deploy a model with tensor parallelism across multiple GPUs (vLLM `--tensor-parallel-size`). Benchmark scaling: 1 GPU vs 2 vs 4. Enable CUDA graphs and measure latency improvement. Profile GPU utilization with `nvidia-smi` and `torch.profiler`.
- **Hour 3 Challenge:** Find the optimal parallelism configuration for a 70B model on 4x A100-40GB (quantization level + tensor parallelism degree). **Interview Q:** "You have a cluster of 32 A100-80GB GPUs. Design a serving infrastructure for 3 different models (7B, 13B, 70B) with different SLAs. How do you allocate GPUs and handle demand spikes?"

### Day 155 — Edge & On-Device Deployment: ONNX, llama.cpp, MLX
- **Hour 1 Theory:** Edge deployment motivations: latency, privacy, cost, offline access. Model export formats: ONNX (cross-platform), CoreML (Apple), TFLite (Android). ONNX Runtime: graph optimizations, quantization, platform-specific accelerators. llama.cpp: C++ inference for GGUF models, CPU + Metal/CUDA. MLX: Apple Silicon ML framework (unified memory). ExecuTorch: PyTorch for mobile. Optimization techniques: operator fusion, memory planning, weight sharing. Model size budgets for mobile: 500MB-2GB typical.
- **Hour 2 Code:** Export a model to ONNX and optimize with ONNX Runtime. Run a GGUF model with llama.cpp and benchmark. Run a model with MLX on Mac. Compare inference speed and quality across all three.
- **Hour 3 Challenge:** Deploy a quantized LLM that runs entirely on your laptop with <1 second TTFT and interactive generation speed. **Interview Q:** "Design an offline-capable AI assistant for field workers in areas with no internet. The app runs on Android tablets with 8GB RAM. Cover: model selection, optimization, on-device storage, and sync-when-connected updates."

### Day 156 — Caching Strategies: Semantic Cache, KV-Cache Sharing & CDN
- **Hour 1 Theory:** Caching layers: exact match cache (hash-based), semantic cache (embedding similarity), KV-cache sharing (prefix cache in serving engine). Semantic cache: embed query → find similar past query → return cached response if similarity > threshold. Cache invalidation: TTL, model version, explicit invalidation. Cache warming: pre-populate with common queries. CDN for static model artifacts. Cost analysis: cache hit saves $0.01-$0.10 per query.
- **Hour 2 Code:** Implement a semantic cache with Redis + sentence-transformers: embed query → search similar → return if match. Add TTL and model version invalidation. Measure cache hit rate and cost savings on a realistic query distribution.
- **Hour 3 Challenge:** Build a multi-layer cache: exact match → semantic cache → KV-prefix cache → full generation. Measure end-to-end cost reduction. **Interview Q:** "Your LLM API costs $200K/month. Analysis shows 40% of queries are semantically similar. Design a caching strategy that could reduce costs to $80K. Discuss cache architecture, invalidation, and quality risks."

### Day 157 — Load Balancing, Auto-Scaling & Traffic Management
- **Hour 1 Theory:** Load balancing for LLM services: challenges (variable request latency, different prompt lengths). Algorithms: round-robin, least-connections, least-tokens-in-flight, shortest-queue. Kubernetes HPA: scale pods based on GPU utilization, queue depth, or custom metrics. KEDA: event-driven autoscaling. Scaling challenges: GPU startup time (minutes), model loading time. Queue-based scaling: manage request queue, scale workers based on queue depth. Cost optimization: spot/preemptible instances (handle interruptions), reserved instances for baseline. Multi-region deployment.
- **Hour 2 Code:** Implement a load balancer for multiple vLLM instances: least-tokens-in-flight routing, health checks, circuit breaker. Set up Kubernetes HPA with custom GPU utilization metric. Implement a request queue with priority levels.
- **Hour 3 Challenge:** Simulate a traffic spike (10x normal) and verify your auto-scaling handles it within SLA. **Interview Q:** "Your LLM service has unpredictable traffic: 100 req/min baseline, but spikes to 10K req/min during product launches. Design the auto-scaling architecture with cost optimization (can't just keep 10K req/min capacity idle)."

### Day 158 — Prompt Management: Versioning, Testing & Optimization
- **Hour 1 Theory:** Prompt-as-code: version control prompts alongside application code. Prompt registry: centralized storage with versioning, rollback, and access control. A/B testing prompts: split traffic, measure quality metrics, statistical significance. Automated prompt optimization: DSPy (compile prompts from examples), TextGrad (gradient-based prompt optimization), OPRO (LLM-based prompt optimization). Prompt templates with variables. Prompt injection testing as part of CI/CD.
- **Hour 2 Code:** Build a prompt management system: file-based storage with Git, CLI for testing prompts against evaluation datasets, A/B testing framework with statistical analysis. Implement DSPy optimization for a classification task.
- **Hour 3 Challenge:** Optimize a RAG system prompt using DSPy: define metric, provide examples, compile optimized prompt. Measure improvement. **Interview Q:** "Your company has 200 prompts across 30 products. When GPT-4o-mini was released, 30% of prompts degraded. Design the prompt management and testing infrastructure that prevents this."

### Day 159 — Evaluation in Production: Online Metrics, Monitoring & Alerting
- **Hour 1 Theory:** Online evaluation: LLM-as-judge on sampled responses, user feedback (thumbs up/down), implicit signals (response regeneration, session length, follow-up questions). Quality metrics: faithfulness, helpfulness, safety, coherence. Monitoring stack: Prometheus for metrics, Grafana for dashboards, PagerDuty for alerting. Key metrics to track: latency (p50/p95/p99), error rate, token usage, cost per query, quality score (rolling average), cache hit rate. Anomaly detection on quality metrics. Drift detection for input distribution changes.
- **Hour 2 Code:** Build a production monitoring pipeline: log all requests/responses → sample for quality evaluation (LLM-as-judge) → compute rolling metrics → Prometheus metrics → Grafana dashboard → alerts for quality degradation. Implement user feedback collection.
- **Hour 3 Challenge:** Simulate a quality degradation scenario (e.g., model update causes regression) and verify your alerting detects it within 30 minutes. **Interview Q:** "Your LLM system's quality degrades gradually over 2 weeks. Users haven't complained yet, but internal metrics show a 15% drop. Design the detection, diagnosis, and remediation system."

### Day 160 — Cost Engineering & FinOps for LLM Systems
- **Hour 1 Theory:** LLM cost anatomy: input tokens (cheaper), output tokens (expensive), fine-tuning compute, serving infrastructure, vector database, observability tools. Cost optimization hierarchy: (1) Route to cheapest capable model (cascade routing), (2) Cache repeated queries, (3) Reduce input tokens (prompt compression, fewer few-shot examples), (4) Reduce output tokens (constrained generation), (5) Fine-tune small model to replace prompted large model, (6) Self-host vs API. Cost monitoring: per-team, per-feature, per-user attribution. Budget alerts and hard limits.
- **Hour 2 Code:** Build a cost engineering dashboard: track cost per query, per feature, per team. Implement cascade routing (classify query difficulty → route to appropriate model). Implement prompt compression (remove redundant context). Calculate ROI of fine-tuning vs prompting.
- **Hour 3 Challenge:** Analyze your Phase 5 agent system's cost. Propose and implement optimizations to reduce cost by 50%. **Interview Q:** "You're the engineering manager for an AI platform. The CEO asks: 'Why does AI cost us $1M/month?' Build the FinOps framework: cost attribution, optimization roadmap, and reporting."

---

## Week 23–24: MLOps for LLMs (Days 161–170)

### Day 161 — ML Pipeline Orchestration: Airflow, Dagster & Prefect
- **Hour 1 Theory:** ML pipeline requirements: DAG orchestration, retries, monitoring, data lineage, scheduling. Airflow: DAGs with operators, XComs for data passing, connections for external systems. Dagster: software-defined assets, type system, IO managers. Prefect: Pythonic workflows, dynamic task creation. Choosing between them: team size, complexity, existing infrastructure. Pipeline patterns: training pipeline, evaluation pipeline, deployment pipeline, data processing pipeline.
- **Hour 2 Code:** Build an ML training pipeline in Dagster: ingest data → validate → preprocess → train → evaluate → register model → deploy (conditional). Implement retry logic and alerting on failure.
- **Hour 3 Challenge:** Build an automated retraining pipeline that triggers when data drift is detected. **Interview Q:** "Design the ML pipeline infrastructure for a team of 50 ML engineers. Cover: pipeline definition, scheduling, monitoring, resource management, and multi-tenancy."

### Day 162 — Experiment Tracking: MLflow, Weights & Biases, Neptune
- **Hour 1 Theory:** Experiment tracking requirements: parameters, metrics, artifacts, code version, data version, model version. MLflow: tracking server, model registry, model serving. Weights & Biases: rich visualization, sweeps (hyperparameter search), artifacts, reports. Neptune: experiment comparison, metadata management. Reproducibility: logging random seeds, environment, data hash, git commit.
- **Hour 2 Code:** Set up MLflow tracking server. Log a complete training run: hyperparameters, learning curves, model checkpoints, evaluation results, confusion matrix, SHAP plots. Implement hyperparameter sweep with WandB Sweeps.
- **Hour 3 Challenge:** Build a custom experiment dashboard that compares multiple runs with statistical significance testing. **Interview Q:** "Your team runs 500 experiments per month. How do you prevent 'experiment rot' (abandoned, unreproducible experiments)? Design the experiment lifecycle management system."

### Day 163 — Model Registry, Version Control & Artifact Management
- **Hour 1 Theory:** Model registry: centralized store for model versions with metadata, lifecycle stages (staging, production, archived), approval workflows. Model versioning: semantic versioning for models (major: architecture change, minor: retrained, patch: config update). Artifact management: model weights, tokenizers, configs, evaluation reports. Model lineage: trace from production model back to training data and code. Model cards: documentation standard for models (intended use, limitations, evaluation, ethical considerations).
- **Hour 2 Code:** Set up MLflow Model Registry. Implement model lifecycle: register → staging → approval → production → archival. Create model cards for your models. Implement automated promotion based on evaluation criteria.
- **Hour 3 Challenge:** Build an automated model promotion pipeline: new model trained → evaluate against production model → if better (statistically significant), promote → notify team. **Interview Q:** "Design a model registry for a company deploying 200 models across 50 services. Cover: versioning, dependencies between models, rollback, compliance requirements, and multi-region deployment."

### Day 164 — CI/CD for ML: Automated Testing & Deployment
- **Hour 1 Theory:** CI/CD for ML adds: data validation, model validation, performance regression testing. Testing pyramid: unit tests (data transforms, feature engineering) → integration tests (pipeline end-to-end) → model tests (accuracy thresholds, bias checks) → system tests (latency, throughput). GitHub Actions / GitLab CI for ML. Progressive deployment: shadow mode → canary → full rollout. Rollback criteria: latency regression, quality drop, error rate spike.
- **Hour 2 Code:** Build a CI/CD pipeline with GitHub Actions: lint → unit tests → train model → evaluate → compare with baseline → deploy to staging → run integration tests → promote to production (manual gate). Implement automated rollback.
- **Hour 3 Challenge:** Add ML-specific checks: data quality validation, model performance threshold, bias detection, latency benchmark. **Interview Q:** "Your team deploys ML models 5 times per week. Last week, a model deployment caused a 30% revenue drop (detected 6 hours later). Design the deployment safety system: testing, canary, monitoring, and automated rollback."

### Day 165 — Data Versioning, Lineage & Governance
- **Hour 1 Theory:** Data versioning: DVC (Data Version Control) — git-like version control for large files. LakeFS: git-like branching for data lakes. Delta Lake: ACID transactions on data lakes. Data lineage: tracking data transformations from source to model prediction. Metadata management: Apache Atlas, DataHub. Data governance: access control, PII management, retention policies, compliance (GDPR, CCPA). Data catalogs for discoverability.
- **Hour 2 Code:** Set up DVC for a project: track data files, create data pipelines, push to remote storage (S3/GCS). Implement data lineage tracking: record every transformation with input/output hashes. Build a simple data catalog.
- **Hour 3 Challenge:** Reproduce a model from 3 months ago using versioned data, code, and configuration. **Interview Q:** "A regulatory audit asks you to prove that a model used for credit scoring was not trained on discriminatory data. Design the data governance system that enables this."

### Day 166 — Feature Stores & Feature Engineering for LLM Apps
- **Hour 1 Theory:** Feature stores: centralized repository for feature definitions, computation, and serving. Online (low latency) vs offline (batch) features. Feast: open-source feature store. Tecton: managed feature platform. Feature engineering for LLM applications: user context features, conversation features, retrieval features. Feature pipelines: batch (Spark), streaming (Flink, Kafka), on-demand. Feature freshness and consistency guarantees.
- **Hour 2 Code:** Set up Feast feature store. Define features for an LLM application: user profile features, conversation history features, retrieval relevance features. Implement a feature pipeline that serves features to your RAG system.
- **Hour 3 Challenge:** Build a personalized RAG system that uses real-time user features to customize retrieval and generation. **Interview Q:** "Design a feature platform for an LLM-powered recommendation system serving 50M users. Features include: user embeddings (updated daily), session features (real-time), and content features (near real-time). Discuss consistency and freshness."

### Day 167 — Monitoring & Observability: Prometheus, Grafana & OpenTelemetry
- **Hour 1 Theory:** Observability three pillars: metrics (Prometheus), logs (ELK/Loki), traces (Jaeger/Zipkin). OpenTelemetry: vendor-neutral standard. ML-specific metrics: prediction distribution shift, feature value drift, model confidence distribution. Grafana dashboards: designing effective ML monitoring views. Alert design: avoid alert fatigue, actionable alerts. SLOs and SLIs for ML: availability, latency, quality. Error budgets.
- **Hour 2 Code:** Set up Prometheus + Grafana for your LLM service. Instrument with custom metrics: request latency histogram, token usage counter, model confidence gauge, error rate. Create dashboards and alerts. Add OpenTelemetry tracing for end-to-end request visibility.
- **Hour 3 Challenge:** Build a "war room" dashboard that shows everything needed to diagnose a production ML incident in real-time. **Interview Q:** "Design the monitoring stack for a platform serving 100 ML models. What metrics do you track, how do you avoid alert fatigue, and how do you ensure coverage for silent failures?"

### Day 168 — Drift Detection: Data Drift, Concept Drift & Quality Degradation
- **Hour 1 Theory:** Types of drift: data/covariate drift (input distribution changes), concept drift (relationship between input and output changes), prediction drift (output distribution changes), feature drift. Detection methods: KS test, PSI (Population Stability Index), JS divergence, ADWIN (adaptive windowing). Reference window vs sliding window. Drift in LLM systems: topic drift, user population change, knowledge staleness. Response to drift: retrain, recalibrate, alert, investigate.
- **Hour 2 Code:** Implement drift detection for an ML system: compute PSI for features, KS test for predictions, embedding drift for text inputs. Build automated drift monitoring with alerts. Implement a drift dashboard.
- **Hour 3 Challenge:** Simulate different types of drift and verify your system detects each. Calculate detection latency. **Interview Q:** "Your production model's accuracy dropped 10% over 2 months but no one noticed until a customer complained. Design the drift detection and response system. How quickly should you detect a 5% accuracy drop?"

### Day 169 — Incident Response & Reliability Engineering for ML
- **Hour 1 Theory:** ML incident taxonomy: model quality regression, data pipeline failure, serving infrastructure issue, security breach, cost spike. Incident response framework: detect → triage → mitigate → resolve → postmortem. Mitigation playbook: rollback model, switch to fallback, disable feature, increase human review. On-call for ML systems. Postmortem template: timeline, root cause, impact, remediation, prevention. SLAs for ML: uptime, quality floor, latency ceiling. Chaos engineering for ML: intentionally inject failures.
- **Hour 2 Code:** Build an incident response automation: detect anomaly → classify severity → execute mitigation playbook (auto-rollback for P0) → notify on-call → create incident ticket. Implement automated rollback to previous model version.
- **Hour 3 Challenge:** Run a "game day": inject various failures into your system and practice incident response. Time yourself. **Interview Q:** "Your recommendation model started showing NSFW content to users at 2 AM. Walk through the complete incident response from detection to postmortem. How do you prevent recurrence?"

### Day 170 — Compliance, Governance & AI Ethics
- **Hour 1 Theory:** Regulatory landscape: EU AI Act (risk classification, transparency requirements), GDPR (right to explanation, data deletion), CCPA, industry-specific regulations (healthcare: HIPAA, finance: SR 11-7). Model documentation: model cards (Mitchell et al.), datasheets for datasets. Fairness metrics: demographic parity, equalized odds, calibration. Bias auditing: pre-training, in-training, post-training. Explainability requirements for high-risk AI. AI governance framework: roles, processes, tools.
- **Hour 2 Code:** Implement a fairness audit: evaluate model predictions across demographic groups, compute fairness metrics, generate a bias report. Create a comprehensive model card. Build an automated compliance check pipeline.
- **Hour 3 Challenge:** Audit one of your models for bias and create a remediation plan. **Interview Q:** "You're the AI governance lead at a bank. Regulators require model explainability for every loan decision made by your ML system. Design the technical and organizational solution."

---

## Week 25–26: System Design & Career Readiness (Days 171–180)

### Day 171 — System Design: Real-Time Recommendation Engine
- **Hour 1 Theory:** Full architecture: candidate generation (two-tower model, collaborative filtering) → ranking (deep ranking model with features) → reranking (business rules, diversity, freshness) → serving. Feature engineering: user features, item features, interaction features, contextual features. Training: implicit feedback, position bias debiasing. Serving: pre-compute for candidates, real-time for ranking. A/B testing for recommendations.
- **Hour 2 Code:** Implement a simplified recommendation system: two-tower model for candidate generation, feature-based ranking model, FastAPI serving with sub-50ms latency.
- **Hour 3 Challenge:** Design the complete system on a whiteboard (no code, just architecture). **Interview Q (Full Rubric):** "Design a recommendation system for YouTube serving 2B users." **Strong Hire Rubric:** (1) Clearly defines requirements and constraints, (2) Proposes candidate generation + ranking + reranking cascade, (3) Discusses feature engineering in depth, (4) Addresses cold start, (5) Designs for sub-100ms latency at scale, (6) Discusses A/B testing and evaluation, (7) Considers fairness and filter bubbles.

### Day 172 — System Design: Search Engine with Semantic Understanding
- **Hour 1 Theory:** Modern search: query understanding → retrieval (BM25 + dense) → ranking cascade → presentation. Query understanding: intent classification, entity extraction, query expansion. Retrieval: inverted index + ANN index, hybrid scoring. Ranking cascade: L0 (BM25), L1 (bi-encoder), L2 (cross-encoder), L3 (LLM reranker). LLM-augmented search: query rewriting, answer generation, snippet extraction.
- **Hour 2 Code:** Build a search engine: Elasticsearch for BM25 + FAISS for dense retrieval + cross-encoder reranking + LLM-generated answers with citations.
- **Hour 3 Challenge:** Design the architecture from scratch on a whiteboard. **Interview Q (Full Rubric):** "Design Google Search for 2026 with LLM-powered features." **Strong Hire Rubric:** (1) Defines the search pipeline clearly, (2) Proposes hybrid retrieval with fusion, (3) Addresses ranking cascade with latency budgets, (4) Discusses LLM integration for answers/summarization, (5) Designs indexing pipeline for freshness, (6) Addresses evaluation (NDCG, MRR, user engagement), (7) Discusses cost of LLM calls at scale.

### Day 173 — System Design: Real-Time Fraud Detection with ML & LLMs
- **Hour 1 Theory:** Fraud detection requirements: <50ms latency, <0.01% false negative rate, minimal false positives. Architecture: rule engine (fast, interpretable) → ML model (catches novel patterns) → LLM (explains decisions, handles edge cases). Feature engineering: velocity features, graph features (connected accounts), behavioral features. Challenges: extreme class imbalance, adversarial adaptation, regulatory requirements.
- **Hour 2 Code:** Build a fraud detection prototype: feature pipeline → gradient boosting model → LLM explainer for flagged transactions.
- **Hour 3 Challenge:** Design the complete system on a whiteboard. **Interview Q (Full Rubric):** "Design a fraud detection system for Stripe processing 10M transactions/day." **Strong Hire Rubric:** (1) Defines latency and accuracy constraints, (2) Proposes multi-model cascade, (3) Addresses class imbalance strategies, (4) Designs real-time feature computation, (5) Discusses concept drift and model updates, (6) Addresses regulatory requirements (explainability), (7) Designs the human review workflow.

### Day 174 — System Design: Autonomous Coding Assistant (Copilot)
- **Hour 1 Theory:** Copilot architecture: IDE extension → context gathering (open files, cursor position, project structure, recent edits) → prompt construction → model serving → response streaming → inline rendering. Context selection: which files/functions are most relevant (TF-IDF, embedding similarity, graph-based). Multi-step code generation: plan → generate → test → iterate. Personalization: user coding style, frequently used APIs.
- **Hour 2 Code:** Build a simplified code assistant: collect context from a project → construct prompt with relevant context → generate completion → apply diff.
- **Hour 3 Challenge:** Design the complete system on a whiteboard. **Interview Q (Full Rubric):** "Design GitHub Copilot." **Strong Hire Rubric:** (1) Defines context gathering strategy, (2) Proposes context ranking/selection, (3) Addresses latency requirements (<300ms), (4) Designs model serving for millions of developers, (5) Discusses evaluation (acceptance rate, productivity impact), (6) Addresses security (not suggesting secrets/vulnerable code), (7) Discusses privacy (code not leaked between organizations).

### Day 175 — System Design: Multi-Tenant LLM Platform
- **Hour 1 Theory:** Platform requirements: multiple teams, different models, custom fine-tunes, usage quotas, access control. Architecture: API gateway → model router → serving cluster → model registry → observability. Multi-tenancy: shared infrastructure with isolation (namespace, quotas, network policies). LoRA serving: multiple LoRA adapters with shared base model (S-LoRA). Cost attribution: track token usage per team/project. Self-service: UI for fine-tuning, deployment, evaluation.
- **Hour 2 Code:** Build a multi-tenant API: team authentication → model selection → LoRA adapter loading → generation → usage tracking per team.
- **Hour 3 Challenge:** Design the complete platform on a whiteboard. **Interview Q (Full Rubric):** "Design an internal LLM platform for a 10,000-person company." **Strong Hire Rubric:** (1) Defines user personas and use cases, (2) Proposes multi-model serving architecture, (3) Addresses LoRA serving for custom models, (4) Designs self-service fine-tuning workflow, (5) Implements cost attribution and budgeting, (6) Addresses security and access control, (7) Designs for platform team of 5 engineers.

### Day 176 — System Design: Document Intelligence Pipeline
- **Hour 1 Theory:** Document pipeline: ingestion (PDF, DOCX, images, HTML) → extraction (OCR, layout analysis, table detection) → classification → entity extraction → storage → search & retrieval. OCR: Tesseract, cloud APIs, PaddleOCR. Layout analysis: detecting headers, paragraphs, tables, figures. Table extraction: structure recognition, cell content extraction. LLM-based extraction: parse unstructured text into structured data.
- **Hour 2 Code:** Build a document processing pipeline: PDF loader → OCR (if scanned) → layout detection → chunk by section → extract entities → store in structured + vector database.
- **Hour 3 Challenge:** Design the complete system on a whiteboard. **Interview Q (Full Rubric):** "Design a document intelligence platform for a law firm processing 100K documents/day." **Strong Hire Rubric:** (1) Defines document types and extraction requirements, (2) Proposes multi-stage processing pipeline, (3) Addresses accuracy requirements (OCR errors, extraction errors), (4) Designs for throughput and cost, (5) Discusses multi-lingual support, (6) Addresses search and retrieval over processed documents, (7) Designs human review workflow for low-confidence extractions.

### Day 177 — MAANG Mock Interview: ML System Design Deep Dive
- **Hour 1 Theory:** ML system design interview framework: (1) Clarify requirements (5 min), (2) Define metrics (5 min), (3) High-level architecture (10 min), (4) Deep dive on key components (15 min), (5) Scaling and operational concerns (5 min), (6) Extensions and trade-offs (5 min). Common mistakes: jumping to solution, over-engineering, ignoring data/evaluation, not discussing trade-offs.
- **Hour 2 Code:** Practice solving: "Design a content moderation system for Instagram that processes 100M posts/day including text, images, and videos."
- **Hour 3 Challenge:** Cold practice: "Design a real-time language translation system for video calls." Time yourself to 45 minutes. Record and review. **Interview Q:** Self-evaluate using the Strong Hire rubric: requirements, architecture, data, ML model, evaluation, serving, operational concerns.

### Day 178 — MAANG Mock Interview: ML Coding & Theory
- **Hour 1 Theory:** ML coding interview patterns: implement from scratch (logistic regression, k-means, attention), debug ML code, optimize existing code, design ML components. Theory questions: loss functions, optimization, regularization, information theory, architecture design decisions.
- **Hour 2 Code:** Practice: (1) Implement multi-head attention from scratch in 30 minutes. (2) Debug a broken training loop (provided with subtle bugs). (3) Optimize a slow inference pipeline.
- **Hour 3 Challenge:** Cold practice: (1) "Implement beam search for a language model" in 25 minutes. (2) "Your model has 95% train accuracy and 60% val accuracy. The PM says add more data. Is this the right approach? Discuss with mathematical rigor." (3) "Derive the gradient of the attention mechanism with respect to Q."

### Day 179 — MAANG Mock Interview: Behavioral & Technical Leadership
- **Hour 1 Theory:** Principal Engineer behavioral interview expectations: technical vision, influence without authority, cross-team impact, mentoring, navigating ambiguity, making bets. STAR format with focus on impact and learning. Common questions: biggest technical bet, dealing with failure, influencing a reluctant team, balancing technical debt vs features.
- **Hour 2 Code:** Write out 8 detailed STAR stories covering: (1) Technical leadership, (2) Conflict resolution, (3) Project failure and recovery, (4) Cross-team influence, (5) Mentoring, (6) Making architectural decisions under uncertainty, (7) Prioritization, (8) Handling disagreement with leadership.
- **Hour 3 Challenge:** Practice delivering 3 stories out loud (record yourself). Get feedback on clarity, impact quantification, and technical depth. **Interview Q:** "Tell me about a time you made a technical decision that the team disagreed with, but turned out to be right. How did you handle the disagreement and what did you learn?"

### Day 180 — Grand Finale: Portfolio, Career Strategy & Next Steps
- **Hour 1 Theory:** Portfolio construction: select 3-5 best projects, write compelling descriptions, highlight impact and technical depth. Resume for AI/ML roles: focus on models, scale, and impact. GitHub profile optimization. Technical blog writing: share your knowledge. Personal brand: Twitter/LinkedIn presence. Networking in AI/ML: conferences (NeurIPS, ICML, local meetups), open-source contributions. Interview preparation strategy: spaced repetition for theory, weekly mock interviews.
- **Hour 2 Code:** Build your portfolio website/page: (1) RAG system from Phase 3/5, (2) Fine-tuned LLM from Phase 4, (3) Agent system from Phase 5, (4) Production deployment from Phase 6. Write README files with architecture diagrams. Record demo videos. Push all code to GitHub with clean commit history.
- **Hour 3 Challenge:** Final assessment: answer 10 random interview questions from the curriculum (2 from each phase, drawn randomly). Time yourself. Grade honestly. **Final Interview Q:** "You have 30 minutes. Design a system that uses LLMs, agents, RAG, and fine-tuning to build an AI-powered analyst that can answer any question about a company's internal data. Start from requirements, end at production deployment."

---

# ═══════════════════════════════════════════════════════════════
# APPENDICES
# ═══════════════════════════════════════════════════════════════

## Appendix A: Required Tools & Environment Setup

### Phase 1–2 Setup (Day 1)
```bash
# Python Environment (use 3.10+ for best compatibility)
python -m venv ai-masterplan
source ai-masterplan/bin/activate  # macOS/Linux
# ai-masterplan\Scripts\activate   # Windows

# Core ML/DL
pip install numpy scipy matplotlib scikit-learn
pip install torch torchvision torchaudio
pip install pandas polars seaborn plotly
pip install jupyter ipywidgets tqdm
pip install pytest hypothesis

# Experiment tracking
pip install mlflow wandb tensorboard
```

### Phase 3–4 Setup (Day 61)
```bash
# Transformers & NLP
pip install transformers datasets tokenizers accelerate
pip install peft trl bitsandbytes
pip install sentence-transformers
pip install evaluate rouge-score sacrebleu

# Serving
pip install vllm
pip install openai anthropic

# RAG & Vector Search
pip install faiss-cpu  # or faiss-gpu
pip install chromadb qdrant-client
pip install langchain langchain-openai langchain-community
pip install ragas deepeval
```

### Phase 5 Setup (Day 121)
```bash
# Agentic AI
pip install langgraph langsmith
pip install crewai crewai-tools
pip install fastmcp

# Tools & Utilities
pip install playwright beautifulsoup4 trafilatura
pip install pydantic instructor outlines
pip install redis
```

### Phase 6 Setup (Day 151)
```bash
# MLOps
pip install dagster dagster-webserver
pip install dvc dvc-s3
pip install feast

# Infrastructure
pip install docker kubernetes
pip install prometheus-client
pip install opentelemetry-api opentelemetry-sdk
pip install fastapi uvicorn httpx
pip install locust  # load testing
```

### IDE & Tools
```bash
# Recommended IDE: VSCode or Cursor
# Extensions: Python, Jupyter, GitLens, Thunder Client

# Git setup
git init ai-masterplan-code
cd ai-masterplan-code
git remote add origin <your-repo-url>

# Directory structure
mkdir -p {phase1,phase2,phase3,phase4,phase5,phase6}/{day{001..030},day{031..060},day{061..090},day{091..120},day{121..150},day{151..180}}
```

---

## Appendix B: Hardware Recommendations

| Level | GPU | VRAM | Use Case | Estimated Cost |
|---|---|---|---|---|
| **Starter** | None (CPU) | — | Days 1–30, classical ML | Free |
| **Intermediate** | RTX 3090/4090 | 24GB | Days 31–90, small model training | $1,500-$2,000 |
| **Advanced** | A100 (cloud) | 40/80GB | Days 91–150, LLM fine-tuning | $1-3/hr cloud |
| **Production** | Multi-GPU cluster | 160GB+ | Days 151–180, serving at scale | $5-20/hr cloud |

### Cloud Provider Comparison

| Provider | GPU | Price (approx) | Best For |
|---|---|---|---|
| **Google Colab Pro+** | A100/L4 | $50/month | Learning, small experiments |
| **Lambda Labs** | A100/H100 | $1.10-$2.50/hr | Training, fine-tuning |
| **RunPod** | A100/H100 | $0.74-$2.39/hr | Training, serving |
| **Vast.ai** | Various | $0.30-$1.50/hr | Budget training |
| **AWS SageMaker** | Various | $1-$30/hr | Enterprise, production |
| **Modal** | A100/H100 | Pay-per-second | Serverless inference |

### Apple Silicon Note
If using a Mac with M1/M2/M3 Pro/Max/Ultra, you can use:
- **MLX** framework for local inference (excellent performance)
- **llama.cpp** with Metal acceleration
- Models up to ~13B parameters (depending on unified memory)
- Not suitable for training large models

---

## Appendix C: Essential Reading List

### Papers (Read in Order, Aligned with Curriculum Days)

| Day | Paper | Why It Matters |
|---|---|---|
| 1–30 | Bishop - PRML (Ch. 1-4) | Mathematical foundations |
| 31–60 | Goodfellow - Deep Learning Book (Ch. 6-11) | Neural network theory |
| 33 | "Automatic Differentiation in ML: a Survey" (Baydin et al., 2018) | Backprop theory |
| 58 | "Denoising Diffusion Probabilistic Models" (Ho et al., 2020) | Diffusion models |
| 61 | "Attention Is All You Need" (Vaswani et al., 2017) | The paper that started it all |
| 68 | "BERT: Pre-training of Deep Bidirectional Transformers" (Devlin et al., 2018) | Bidirectional pre-training |
| 69 | "Language Models are Few-Shot Learners" (GPT-3, Brown et al., 2020) | In-context learning |
| 69 | "Training Compute-Optimal LLMs" (Chinchilla, Hoffmann et al., 2022) | Scaling laws |
| 72 | "FlashAttention" (Dao et al., 2022) | IO-aware attention |
| 79 | "Mixtral of Experts" (Jiang et al., 2024) | MoE architecture |
| 80 | "Mamba: Linear-Time Sequence Modeling" (Gu & Dao, 2023) | Alternative to attention |
| 83 | "Retrieval-Augmented Generation" (Lewis et al., 2020) | RAG foundations |
| 91 | "LLaMA: Open and Efficient Foundation Language Models" (Touvron et al., 2023) | Open LLM architecture |
| 97 | "LoRA: Low-Rank Adaptation" (Hu et al., 2021) | Efficient fine-tuning |
| 98 | "QLoRA: Efficient Finetuning of Quantized LLMs" (Dettmers et al., 2023) | Memory-efficient fine-tuning |
| 103 | "Training Language Models to Follow Instructions (InstructGPT)" (Ouyang et al., 2022) | RLHF pipeline |
| 104 | "Direct Preference Optimization" (Rafailov et al., 2023) | Simpler alignment |
| 115 | "Chain-of-Thought Prompting" (Wei et al., 2022) | LLM reasoning |
| 121 | "ReAct: Synergizing Reasoning and Acting" (Yao et al., 2022) | Agent foundations |
| 125 | Model Context Protocol Specification (Anthropic, 2024) | Tool use standard |
| 151 | "Efficient Memory Management for LLM Serving with PagedAttention" (vLLM, Kwon et al., 2023) | Serving optimization |

### Books

| Book | Author(s) | Best For |
|---|---|---|
| "Mathematics for Machine Learning" | Deisenroth, Faisal, Ong | Phase 1 math foundations |
| "Dive into Deep Learning" (d2l.ai) | Zhang et al. | Phase 2-3 hands-on DL |
| "Deep Learning" | Goodfellow, Bengio, Courville | Phase 2 theory (free online) |
| "Natural Language Processing with Transformers" | Tunstall, von Werra, Wolf | Phase 3 practical NLP |
| "Designing Machine Learning Systems" | Chip Huyen | Phase 6 production ML |
| "Building LLM Powered Applications" | Valentina Alto | Phase 5-6 LLM apps |
| "Hands-On Large Language Models" | Alammar, Grootendorst | Phase 3-4 practical LLMs |

---

## Appendix D: Weekly Assessment Protocol

Every 7th day (Days 7, 14, 21, 28, ...) includes a review session:

| Assessment | Weight | Format |
|---|---|---|
| **Concept Map** | 20% | Draw dependency graph of the week's concepts from memory |
| **Code Portfolio** | 40% | All implementations passing tests, committed to repo with docstrings |
| **Interview Answers** | 20% | Written answers to all 6 daily interview questions (min 300 words each) |
| **Solo Challenge** | 20% | Complete at least 4/6 solo challenges without reference |

### Grading Scale
- **≥90%:** On track for Staff+ level. Keep pushing.
- **70–89%:** Solid Senior Engineer trajectory. Focus on weak areas.
- **50–69%:** Revisit weak areas before proceeding. Re-do 2 weakest days.
- **<50%:** Repeat the week. No shame — mastery requires repetition.

### Monthly Deep Review (Days 30, 60, 90, 120, 150, 180)
- [ ] Can explain all major concepts from the phase without notes
- [ ] All code from the phase runs and passes tests
- [ ] Completed at least 80% of solo challenges
- [ ] Written answers for all interview questions
- [ ] Can do a 30-minute mock interview covering the phase

---

## Appendix E: Progress Tracking

```
Phase 1: Days 001–030 [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%  ___/30 days
Phase 2: Days 031–060 [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%  ___/30 days
Phase 3: Days 061–090 [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%  ___/30 days
Phase 4: Days 091–120 [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%  ___/30 days
Phase 5: Days 121–150 [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%  ___/30 days
Phase 6: Days 151–180 [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%  ___/30 days

OVERALL:             [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%  ___/180 days
```

### Milestone Tracker

| Milestone | Target Day | Status |
|---|---|---|
| First ML model from scratch | Day 7 | ☐ |
| First neural network | Day 31 | ☐ |
| Transformer from scratch | Day 67 | ☐ |
| First RAG system | Day 83 | ☐ |
| First fine-tuned LLM | Day 97 | ☐ |
| First agent system | Day 121 | ☐ |
| First MCP server | Day 125 | ☐ |
| First production deployment | Day 151 | ☐ |
| Portfolio complete | Day 180 | ☐ |

---

## Appendix F: Glossary of Key Terms

| Term | Definition |
|---|---|
| **Adam** | Adaptive Moment Estimation optimizer combining momentum and RMSProp |
| **Attention** | Mechanism allowing models to focus on relevant parts of input |
| **Autoregressive** | Generating output one token at a time, conditioned on previous tokens |
| **BPE** | Byte Pair Encoding — subword tokenization algorithm |
| **CLIP** | Contrastive Language-Image Pre-training model by OpenAI |
| **DPO** | Direct Preference Optimization — alignment without reward model |
| **FAISS** | Facebook AI Similarity Search — vector index library |
| **FFN** | Feed-Forward Network — position-wise MLP in Transformers |
| **FSDP** | Fully Sharded Data Parallel — distributed training strategy |
| **GQA** | Grouped Query Attention — efficient attention variant |
| **KV-Cache** | Cached key-value tensors for efficient autoregressive generation |
| **LoRA** | Low-Rank Adaptation — parameter-efficient fine-tuning |
| **MCP** | Model Context Protocol — standardized tool integration for LLMs |
| **MoE** | Mixture of Experts — sparse model architecture |
| **PEFT** | Parameter-Efficient Fine-Tuning |
| **PPO** | Proximal Policy Optimization — RL algorithm used in RLHF |
| **QLoRA** | Quantized LoRA — fine-tuning with 4-bit quantized base model |
| **RAG** | Retrieval-Augmented Generation |
| **RLHF** | Reinforcement Learning from Human Feedback |
| **RMSNorm** | Root Mean Square Normalization — simpler than LayerNorm |
| **RoPE** | Rotary Position Embeddings — position encoding for Transformers |
| **SFT** | Supervised Fine-Tuning on instruction data |
| **SwiGLU** | Swish-Gated Linear Unit — FFN variant used in LLaMA |
| **TTFT** | Time to First Token — latency metric for LLM serving |
| **TPOT** | Time per Output Token — throughput metric for LLM serving |
| **vLLM** | High-throughput LLM serving with PagedAttention |

---

## Appendix G: Project Portfolio Guide

By Day 180, you should have these portfolio-ready projects:

### Tier 1: Showcase Projects (Pick 3)
1. **Production RAG System** (Phase 3/5) — Document Q&A with hybrid search, reranking, citations, and evaluation
2. **Fine-Tuned Domain LLM** (Phase 4) — Custom fine-tuned model with QLoRA + DPO alignment + evaluation
3. **Multi-Agent System** (Phase 5) — LangGraph orchestration + MCP tools + CrewAI crews + observability
4. **LLM Serving Platform** (Phase 6) — Multi-model serving with caching, monitoring, and auto-scaling

### Tier 2: Supporting Projects
5. **ML Math Toolkit** (Phase 1) — From-scratch implementations of PCA, SVD, gradient descent, etc.
6. **Transformer From Scratch** (Phase 3) — Complete implementation with attention, FFN, positional encoding
7. **GPT-2 Implementation** (Phase 3) — Working language model with sampling strategies

### Portfolio Presentation
- **GitHub:** Clean repos with README, architecture diagrams, setup instructions
- **Blog Posts:** 3-5 technical posts explaining your projects (Medium, Substack, or personal blog)
- **Demo Videos:** 2-3 minute recordings showing each project in action
- **Architecture Diagrams:** Professional system design diagrams for each project

---

## Appendix H: Community & Resources

### Online Communities
- **Discord:** Weights & Biases, Hugging Face, LangChain, MLOps Community
- **Reddit:** r/MachineLearning, r/LocalLLaMA, r/MLOps
- **Twitter/X:** Follow AI researchers and engineers (Andrej Karpathy, Chip Huyen, Sebastian Raschka)

### Conferences & Meetups
- **Top conferences:** NeurIPS, ICML, ICLR, ACL, EMNLP
- **Workshops:** MLOps World, AI Engineer Summit
- **Local meetups:** Search Meetup.com for ML/AI groups in your city

### Free Learning Resources
- **3Blue1Brown** — Visual math explanations (YouTube)
- **Andrej Karpathy** — Neural network from scratch series (YouTube)
- **Stanford CS229/CS231n/CS224n** — ML, CV, NLP courses (YouTube)
- **fast.ai** — Practical deep learning (free course)
- **Hugging Face NLP Course** — Transformers hands-on (free)

---

## Appendix I: Recommended Udemy & YouTube Courses

To fully grasp the theoretical and practical concepts across the 180 days, use these highly-rated video courses as your primary learning resources alongside the reading list.

### YouTube (Free, Full Courses)
- **Phase 1 (Math & Classical ML):**
  - [StatQuest with Josh Starmer](https://www.youtube.com/user/joshstarmer) — The absolute best for intuitive breakdowns of <abbr title="Machine Learning">ML</abbr> algorithms, PCA, and statistics.
  - [MIT 18.06 Linear Algebra (Gilbert Strang)](https://www.youtube.com/playlist?list=PL49CF3715CB9EF31D) — The gold standard for linear algebra.
  - [Stanford CS229: Machine Learning (Andrew Ng)](https://www.youtube.com/playlist?list=PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU) — Heavy math derivations for classical <abbr title="Machine Learning">ML</abbr>.
- **Phase 2 (Deep Learning):**
  - [Andrej Karpathy's "Neural Networks: Zero to Hero"](https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ) — Build micrograd, makemore, and GPT from scratch. (Mandatory viewing).
  - [Stanford CS231n: CNNs for Visual Recognition](https://www.youtube.com/playlist?list=PL3FW7Lu3i5JvHM8ljYj-zLfQRF3EO8sYv) — Excellent for backprop, CNNs, and computer vision.
- **Phase 3 & 4 (Transformers, <abbr title="Natural Language Processing">NLP</abbr>, & LLMs):**
  - [Stanford CS224n: NLP with Deep Learning](https://www.youtube.com/playlist?list=PLoROMvodv4rOSH4v6133s9LFPRHjEmbmJ) — Covers word vectors to transformers and prompt engineering.
  - [Let's build GPT: from scratch (Karpathy)](https://www.youtube.com/watch?v=kCc8FmEb1nY) — Essential for Day 69.
  - [Umar Jamil's Paper Breakdowns](https://www.youtube.com/@UmarJamilAI) — Excellent for deep dives into LLaMA, <abbr title="Low-Rank Adaptation">LoRA</abbr>, and FlashAttention architectures.
- **Phase 5 & 6 (Agents & MLOps):**
  - [LangChain & CrewAI Official YouTube Channels] — For the latest tutorials on agent orchestration.
  - [Made With ML (Goku Mohandas)](https://www.youtube.com/c/MadeWithML) — Phenomenal free MLOps content (also available on madewithml.com).

### Udemy (Paid, Structured Learning)
- **"Machine Learning A-Z" (Kirill Eremenko & Hadelin de Ponteves)** — Great practical starting point for Phase 1.
- **"Deep Learning A-Z" (Kirill Eremenko & Hadelin de Ponteves)** — Solid coverage of ANN, <abbr title="Convolutional Neural Network">CNN</abbr>, and <abbr title="Recurrent Neural Network">RNN</abbr> implementations.
- **"PyTorch for Deep Learning in 202X: Zero to Mastery" (Daniel Bourke)** — Excellent, code-heavy, practical PyTorch foundation.
- **"Deployment of Machine Learning Models" (Soledad Galli)** — Exceptional for Phase 6 (MLOps, <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr>, <abbr title="A set of platform as a service products that use OS-level virtualization to deliver software in packages called containers.">Docker</abbr>, <abbr title="Application Programming Interface">API</abbr> serving).
- **"Generative <abbr title="Artificial Intelligence">AI</abbr> with Large Language Models" (DeepLearning.<abbr title="Artificial Intelligence">AI</abbr> / Coursera/Udemy)** — Industry-standard course on <abbr title="Large Language Model">LLM</abbr> lifecycle, <abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr>, and fine-tuning.

---

## Appendix J: The Google <abbr title="Artificial Intelligence">AI</abbr> Engineer Track (JAX, TPUs, & Scale)

If you are targeting Google (or DeepMind), you need to supplement the PyTorch-heavy curriculum with Google's internal stack:

1. **JAX & Flax (Days 31-60 Supplement):** 
   - Google heavily relies on JAX for high-performance <abbr title="Machine Learning">ML</abbr>. 
   - Learn JAX transformations: `jax.jit` (Just-In-Time compilation), `jax.grad` (autodiff), `jax.vmap` (vectorization), and `jax.pmap` (parallelization).
   - *Resource:* DeepMind's JAX tutorials on GitHub.
2. **TPU Architecture (Days 91-100 Supplement):**
   - Understand how Tensor Processing Units differ from GPUs (Systolic Arrays, bfloat16 natively).
   - Learn how to distribute training across TPU pods.
3. **Google-Scale System Design (Days 171-176 Focus):**
   - Study Google's specific papers: *Wide & Deep Learning for Recommender Systems*, *TFX (TensorFlow Extended)*, and *Spanner*.
   - Google interviews index heavily on handling latency and throughput at billions-of-users scale.

---

## 🎯 HOW TO USE THIS CURRICULUM

1. **Start on Day 1.** Do not skip ahead. The curriculum is deliberately sequenced — each day builds on previous days.
2. **Ask me to tutor any specific day.** Say: *"Tutor me on Day 46: Multi-Head Attention Math"* and I will deliver the full 3-hour breakdown with:
   - Complete mathematical derivations (LaTeX)
   - Production-grade Python code with type hints and docstrings
   - Solo challenge statement (blank-slate, no copying)
   - MAANG interview question with Strong Hire rubric
3. **Use the Daily Checklist** (above) for every session. Print it. Fill it. Don't skip the reflection.
4. **Track your progress** in Appendix E. Update the progress bars as you complete days.
5. **Do the solo challenges.** The gap between "I understand this" and "I can build this from scratch" is where real learning happens.
6. **Write out interview answers.** Principal Engineers articulate concepts precisely. Practice this daily. Minimum 300 words per answer.
7. **Don't break the chain.** 3 hours every day. If you miss a day, make it up the next day (6 hours). Never miss two days in a row.

---

> *"The difference between a Senior and a Principal Engineer is not what they know — it's the depth at which they know it, and their ability to make it work at scale under real-world constraints."*

---

**Ready to begin? Tell me which day to start tutoring, and I'll deliver the full 3-hour deep dive.** 🚀
