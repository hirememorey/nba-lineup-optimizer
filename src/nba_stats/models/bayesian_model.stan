data {
    int<lower=0> N; // Number of possessions
    int<lower=0> K; // Number of player archetypes
    int<lower=0> M; // Number of matchup types (supercluster combinations)
    
    vector[K] Z_off[N]; // Offensive skill vectors
    vector[K] Z_def[N]; // Defensive skill vectors
    
    real y[N]; // Outcome of each possession (net points)
    
    int<lower=1, upper=M> matchup_indices[N]; // Index for the matchup type for each possession
}

parameters {
    real<lower=0> beta_off[M][K]; // Offensive skill coefficients per matchup-archetype
    real<lower=0> beta_def[M][K]; // Defensive skill coefficients per matchup-archetype
    real alpha[M];               // Intercept for each matchup type
    real<lower=0> sigma;         // Error term
}

model {
    // Priors
    for (m in 1:M) {
        alpha[m] ~ normal(0, 1);
        for (k in 1:K) {
            beta_off[m][k] ~ normal(0, 5); // Weakly-informative prior
            beta_def[m][k] ~ normal(0, 5); // Weakly-informative prior
        }
    }
    sigma ~ cauchy(0, 5);

    // Likelihood
    for (i in 1:N) {
        int m = matchup_indices[i];
        real mu = alpha[m] + dot_product(beta_off[m], Z_off[i]) - dot_product(beta_def[m], Z_def[i]);
        y[i] ~ normal(mu, sigma);
    }
} 