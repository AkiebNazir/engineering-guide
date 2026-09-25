# 18. Data Visualization: Matplotlib & Seaborn

Welcome to the visual side of Machine Learning. Before you can train a model, you must understand your data. If you have 100,000 rows of tabular data, printing `df.head()` isn't enough to find outliers, correlations, or skewed distributions. You must visualize it.

In the Python ecosystem, **Matplotlib** is the bedrock low-level drawing engine, and **Seaborn** is the high-level statistical wrapper built on top of it.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Matplotlib Object Hierarchy
Most beginners get frustrated with Matplotlib because they just copy-paste `plt.plot()` from StackOverflow without understanding the underlying object-oriented architecture.
- **The Figure (`fig`):** The blank canvas. It is the outer window that holds everything.
- **The Axes (`ax`):** A specific plot (or subplot) drawn *on* the canvas. A single Figure can contain multiple Axes.
- **The Artist:** Everything you see (lines, text, ticks, labels) is an "Artist" object attached to the Axes.

### 2. Why Seaborn?
If Matplotlib is HTML, Seaborn is Bootstrap.
To draw a grouped bar chart with error bars in pure Matplotlib requires 20 lines of complex loop logic to calculate the standard deviations and offset the bars. 
In Seaborn, it requires one line: `sns.barplot(data=df, x="category", y="value", hue="group")`. Seaborn automatically calculates the statistical aggregations and applies a beautiful default color palette.

### 3. The Core Visualization Arsenal
For ML engineers, you don't need to know every chart type. You need these five:
1. **Histograms (`sns.histplot`):** To check the distribution of a single feature (is it normally distributed or heavily skewed?).
2. **Box Plots (`sns.boxplot`):** To instantly spot statistical outliers in your dataset.
3. **Scatter Plots (`sns.scatterplot`):** To see the relationship between two continuous variables.
4. **Correlation Heatmaps (`sns.heatmap`):** To see the Pearson correlation coefficient between *all* numerical features at once (critical for identifying multicollinearity before feeding data to a linear model).
5. **Pair Plots (`sns.pairplot`):** To plot every feature against every other feature in a giant grid.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's do a complete Exploratory Data Analysis (EDA) on a mock housing dataset.

Create a file named `eda_visualization.py`:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_eda_visualizations():
    print("--- STARTING EXPLORATORY DATA ANALYSIS ---")
    
    # 1. Generate Mock Housing Data
    np.random.seed(42)
    data = {
        'SquareFeet': np.random.normal(1500, 500, 1000),
        'Age': np.random.uniform(1, 100, 1000),
        'Neighborhood': np.random.choice(['North', 'South', 'East', 'West'], 1000)
    }
    # Price is a function of Size, Age, and some random noise
    data['Price'] = (data['SquareFeet'] * 150) - (data['Age'] * 1000) + np.random.normal(0, 20000, 1000)
    
    df = pd.DataFrame(data)
    
    # SETTING UP THE CANVAS: 2 rows, 2 columns of plots
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(14, 10))
    fig.suptitle('Housing Data Exploratory Analysis', fontsize=16)
    
    # --- PLOT 1: Histogram (Top Left) ---
    # Are most houses big or small?
    sns.histplot(df['Price'], bins=30, kde=True, ax=axes[0, 0], color='skyblue')
    axes[0, 0].set_title('Distribution of House Prices')
    axes[0, 0].set_xlabel('Price ($)')
    
    # --- PLOT 2: Boxplot (Top Right) ---
    # Are prices drastically different depending on the neighborhood? Are there outliers?
    sns.boxplot(data=df, x='Neighborhood', y='Price', ax=axes[0, 1], palette='Set2')
    axes[0, 1].set_title('Prices by Neighborhood')
    
    # --- PLOT 3: Scatter Plot (Bottom Left) ---
    # Does size linearly correlate with price?
    sns.scatterplot(data=df, x='SquareFeet', y='Price', hue='Neighborhood', alpha=0.6, ax=axes[1, 0])
    axes[1, 0].set_title('Square Feet vs. Price')
    
    # --- PLOT 4: Correlation Heatmap (Bottom Right) ---
    # What features actually matter for predicting price?
    # We only compute correlation for numerical columns!
    numerical_df = df[['SquareFeet', 'Age', 'Price']]
    correlation_matrix = numerical_df.corr()
    
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=axes[1, 1])
    axes[1, 1].set_title('Feature Correlation Heatmap')
    
    # Adjust layout so labels don't overlap
    plt.tight_layout()
    
    # Save the massive dashboard to disk
    plt.savefig('housing_eda_dashboard.png', dpi=300)
    print("Dashboard saved to 'housing_eda_dashboard.png'. Open it to see the plots!")
    
    # plt.show() # Uncomment if running in a Jupyter Notebook

if __name__ == "__main__":
    run_eda_visualizations()
```

### Key Takeaways from Code:
1. **The Subplot Architecture:** `plt.subplots(2, 2)` gives us a perfectly managed grid. We just pass `ax=axes[0,0]` into Seaborn, and Seaborn perfectly routes its complex statistical drawing into that specific corner of the canvas.
2. **KDE:** In the histogram, `kde=True` (Kernel Density Estimate) automatically overlays a smoothed line curve over the bar buckets.
3. **Heatmap Interpretation:** In the heatmap, `SquareFeet` and `Price` will show a strong positive correlation (closer to +1.0), while `Age` and `Price` will show a negative correlation (closer to -1.0). This instantly tells us both features are great predictors for an ML model!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Dimensionality Reduction Visualization
You cannot visualize 100-dimensional data on a 2D screen. But you can use PCA (Principal Component Analysis) or t-SNE to compress it to 2D first.
**Your Task:**
1. Import the famous `digits` dataset from `sklearn.datasets`. (It represents 8x8 images of handwritten numbers, which means each image has 64 dimensions).
2. Run `PCA(n_components=2)` on the data.
3. Use a Seaborn scatterplot to plot the 2 Principal Components, coloring the dots (`hue`) by their actual digit label (0-9).
4. See how clearly the different numbers cluster together in 2D space!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are handed a dataset with 500 features and 1 million rows. Your manager wants to know if you can build a Linear Regression model to predict the target variable. What visual EDA (Exploratory Data Analysis) steps do you take before writing any model code, and why?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Target Distribution:** Check the target variable using a histogram. If it is massively skewed (e.g., a few billionaires in a dataset of normal salaries), Linear Regression will perform terribly without a Log-Transformation.
2. **Multicollinearity (Heatmap):** Mention generating a Correlation Heatmap (though for 500 features, you'd filter it programmatically first). If two features are 99% correlated (like `Year_Born` and `Age`), you must drop one to ensure the Linear Regression coefficients remain stable.
3. **Outliers (Boxplots):** Highlight that Linear Regression is highly sensitive to outliers. You would use boxplots on the most correlated features to identify extreme outliers and clip them.

---
**Task for the end of the day:** Commit your code to Git. 

Data visualization is how you debug your data. Tomorrow, we will look at how to deploy these models to production.
