// Stan model for Bayesian regression of NBA possession outcomes
// Equation 2.5 from Brill, Hughes, and Waldbaum

data {
    int<lower=0> N; // number of observations
    vector[N] y;    // outcome variable (net points)
    
    // Z-scores: aggregated skill ratings by archetype
    // We have 8 archetypes (0-7) for each side (offense/defense)
    matrix[N, 8] z_off;
    matrix[N, 8] z_def;
}

parameters {
    real beta_0; // intercept
    
    // Coefficients for offensive and defensive Z-scores.
    // We constrain them to be positive as per the paper's methodology.
    vector<lower=0>[8] beta_off;
    vector<lower=0>[8] beta_def;
    
    // Error term
    real<lower=0> sigma;
}

model {
    // Priors (weakly-informative as described in the paper)
    beta_0 ~ normal(0, 5);
    beta_off ~ normal(0, 5);
    beta_def ~ normal(0, 5);
    sigma ~ cauchy(0, 2.5);
    
    // Likelihood
    // The model predicts the outcome y as a linear combination of the intercept
    // and the dot products of beta coefficients and Z-score vectors.
    y ~ normal(beta_0 + z_off * beta_off - z_def * beta_def, sigma);
} 