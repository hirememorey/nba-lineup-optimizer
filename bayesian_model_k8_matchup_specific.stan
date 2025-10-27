// Stan model for Bayesian regression of NBA possession outcomes WITH matchup-specific coefficients
// Equation 2.5 from Brill, Hughes, and Waldbaum - FULL VERSION

data {
    int<lower=0> N; // number of observations
    int<lower=0> M; // number of unique matchups
    
    vector[N] y;    // outcome variable (net points)
    
    // Matchup indices for each observation
    array[N] int<lower=1, upper=M> matchup;
    
    // Z-scores: aggregated skill ratings by archetype
    matrix[N, 8] z_off;
    matrix[N, 8] z_def;
}

parameters {
    // Intercept per matchup (β₀,m)
    vector[M] beta_0_matchup;
    
    // Coefficients for offensive Z-scores per archetype per matchup (β_off_a,mi)
    // Matrix [archetype, matchup]
    matrix<lower=0>[8, M] beta_off_matchup;
    
    // Coefficients for defensive Z-scores per archetype per matchup (β_def_a,mi)
    matrix<lower=0>[8, M] beta_def_matchup;
    
    // Error term
    real<lower=0> sigma;
}

model {
    // Priors (weakly-informative as described in the paper)
    beta_0_matchup ~ normal(0, 5);
    to_vector(beta_off_matchup) ~ normal(0, 5);
    to_vector(beta_def_matchup) ~ normal(0, 5);
    sigma ~ cauchy(0, 2.5);
    
    // Likelihood with matchup-specific coefficients
    for (n in 1:N) {
        int m = matchup[n];
        real pred = beta_0_matchup[m];
        
        // Sum over archetypes with matchup-specific coefficients
        for (a in 1:8) {
            pred += beta_off_matchup[a, m] * z_off[n, a];
            pred += -beta_def_matchup[a, m] * z_def[n, a];
        }
        
        y[n] ~ normal(pred, sigma);
    }
}

generated quantities {
    // Posterior predictions for new data
    vector[N] y_pred;
    
    for (n in 1:N) {
        int m = matchup[n];
        real pred = beta_0_matchup[m];
        
        for (a in 1:8) {
            pred += beta_off_matchup[a, m] * z_off[n, a];
            pred += -beta_def_matchup[a, m] * z_def[n, a];
        }
        
        y_pred[n] = pred;
    }
}
