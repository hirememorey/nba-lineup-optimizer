data {
  int<lower=1> N;                    // Number of possessions
  int<lower=1> M;                    // Number of unique matchups
  array[N] int<lower=1, upper=M> matchup;  // Matchup index for each possession
  array[N] real outcome;             // Possession outcomes
  array[N] real z_off_0;            // Offensive skill for archetype 0 (Big Men)
  array[N] real z_off_1;            // Offensive skill for archetype 1 (Primary Ball Handlers)
  array[N] real z_off_2;            // Offensive skill for archetype 2 (Role Players)
  array[N] real z_def_0;            // Defensive skill for archetype 0 (Big Men)
  array[N] real z_def_1;            // Defensive skill for archetype 1 (Primary Ball Handlers)
  array[N] real z_def_2;            // Defensive skill for archetype 2 (Role Players)
}

parameters {
  array[M] real beta_0;                 // Matchup-specific intercepts
  array[M, 3] real<lower=0> beta_off;  // Offensive coefficients (must be positive)
  array[M, 3] real<lower=0> beta_def;  // Defensive coefficients (must be positive)
  real<lower=0> sigma;              // Error standard deviation
}

model {
  // Priors
  beta_0 ~ normal(0, 1);               // Weakly informative priors for intercepts
  for (m in 1:M) {
    for (a in 1:3) {
      beta_off[m, a] ~ normal(0, 5);   // Half-normal priors for offensive coefficients
      beta_def[m, a] ~ normal(0, 5);   // Half-normal priors for defensive coefficients
    }
  }
  sigma ~ exponential(1);           // Prior for error standard deviation
  
  // Likelihood
  for (n in 1:N) {
    real mu = beta_0[matchup[n]];
    
    // Add offensive terms
    mu += beta_off[matchup[n], 1] * z_off_0[n];
    mu += beta_off[matchup[n], 2] * z_off_1[n];
    mu += beta_off[matchup[n], 3] * z_off_2[n];
    
    // Subtract defensive terms
    mu -= beta_def[matchup[n], 1] * z_def_0[n];
    mu -= beta_def[matchup[n], 2] * z_def_1[n];
    mu -= beta_def[matchup[n], 3] * z_def_2[n];
    
    outcome[n] ~ normal(mu, sigma);
  }
}

generated quantities {
  array[N] real y_rep;              // Posterior predictive samples
  real log_lik;                     // Log-likelihood for model comparison
  
  log_lik = 0;
  for (n in 1:N) {
    real mu = beta_0[matchup[n]];
    
    // Add offensive terms
    mu += beta_off[matchup[n], 1] * z_off_0[n];
    mu += beta_off[matchup[n], 2] * z_off_1[n];
    mu += beta_off[matchup[n], 3] * z_off_2[n];
    
    // Subtract defensive terms
    mu -= beta_def[matchup[n], 1] * z_def_0[n];
    mu -= beta_def[matchup[n], 2] * z_def_1[n];
    mu -= beta_def[matchup[n], 3] * z_def_2[n];
    
    y_rep[n] = normal_rng(mu, sigma);
    log_lik += normal_lpdf(outcome[n] | mu, sigma);
  }
}
