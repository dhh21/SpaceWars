

def ols(X, Y):
    beta_hat = ((X - X.mean()) * (Y - Y.mean())).sum() / ((X ** 2).sum())
    alpha_hat = Y.mean() - (beta_hat * X.mean())

    residuals = Y - alpha_hat - (beta_hat * X)

    return {'beta_hat': [beta_hat], 'alpha_hat': [alpha_hat]}, residuals


def rmse(residuals): return (residuals ** 2 ).mean() ** .5