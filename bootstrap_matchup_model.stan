
data {
    int<lower=1> N;           // number of observations
    int<lower=1> M;           // number of matchups
    int<lower=1> K;           // number of archetypes
    vector[N] y;              // outcome (net points)
    int<lower=1,upper=M> matchup_id[N];  // matchup index for each observation
    matrix[N,K] z_off;        // offensive archetype aggregates
    matrix[N,K] z_def;        // defensive archetype aggregates
}

parameters {
    real beta_0[M];           // matchup-specific intercepts
    matrix<lower=0>[M,K] beta_off;  // offensive coefficients (positive)
    matrix<lower=0>[M,K] beta_def;  // defensive coefficients (positive)
    real<lower=0> sigma;      // residual standard deviation
}

model {
    // Priors
    beta_0 ~ normal(0, 1);
    for (m in 1:M) {
        beta_off[m] ~ normal(0, 0.5);  // Weak positive prior
        beta_def[m] ~ normal(0, 0.5);  // Weak positive prior
    }
    sigma ~ normal(0, 1);

    // Likelihood
    for (n in 1:N) {
        int m = matchup_id[n];
        real mu = beta_0[m];

        // Add archetype contributions
        for (k in 1:K) {
            mu += beta_off[m,k] * z_off[n,k] - beta_def[m,k] * z_def[n,k];
        }

        y[n] ~ normal(mu, sigma);
    }
}

generated quantities {
    // Log likelihood for model comparison
    vector[N] log_lik;
    for (n in 1:N) {
        int m = matchup_id[n];
        real mu = beta_0[m];

        for (k in 1:K) {
            mu += beta_off[m,k] * z_off[n,k] - beta_def[m,k] * z_def[n,k];
        }

        log_lik[n] = normal_lpdf(y[n] | mu, sigma);
    }
}
