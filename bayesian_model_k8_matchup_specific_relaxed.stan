// Matchup-Specific Model - RELAXED VERSION
// Removes strict lower=0 constraints that cause divergence
// Allows negative coefficients to explore parameter space

data {
    int<lower=0> N; 
    vector[N] y;
    array[N] int<lower=0, upper=35> matchup_id;
    matrix[N, 8] z_off;
    matrix[N, 8] z_def;
}

parameters {
    // Matchup-specific intercepts (36 matchups)
    vector[36] beta_0;

    // REMOVED <lower=0> constraint to reduce divergent transitions
    matrix[36, 8] beta_off;  // Can be negative to explore parameter space
    matrix[36, 8] beta_def;  // Can be negative

    // Error term
    real<lower=0> sigma;
}

model {
    // Priors (weaker than before)
    beta_0 ~ normal(0, 5);
    for (m in 1:36) {
        beta_off[m] ~ normal(0, 5);
        beta_def[m] ~ normal(0, 5);
    }
    sigma ~ cauchy(0, 2.5);

    // Likelihood
    for (i in 1:N) {
        int m = matchup_id[i] + 1;
        real pred = beta_0[m] +
                   sum(z_off[i] .* beta_off[m]) -
                   sum(z_def[i] .* beta_def[m]);
        y[i] ~ normal(pred, sigma);
    }
}

generated quantities {
    vector[N] y_pred;
    vector[N] log_lik;

    for (i in 1:N) {
        int m = matchup_id[i] + 1;
        real pred = beta_0[m] +
                   sum(z_off[i] .* beta_off[m]) -
                   sum(z_def[i] .* beta_def[m]);
        y_pred[i] = normal_rng(pred, sigma);
        log_lik[i] = normal_lpdf(y[i] | pred, sigma);
    }
}

