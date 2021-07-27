from operator import indexOf

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from simple_linear_regression import ols, rmse


class L_method():

    def __init__(self):
        pass


    def fit(self, data, column_name):
        self.current_knee = data.shape[0] // 10
        self._last_knee = self.current_knee
        self._cutoff = self.current_knee

        self.lefts = pd.DataFrame({'beta_hat': [], 'alpha_hat': []})
        self.rights = pd.DataFrame({'beta_hat': [], 'alpha_hat': []})

        self.error = []

        self._n = self.current_knee

        self._column_name = column_name

        while (True):

            self._last_knee = self.current_knee

            self.error = []
            self.lefts = pd.DataFrame({'beta_hat': [], 'alpha_hat': []})
            self.rights = pd.DataFrame({'beta_hat': [], 'alpha_hat': []})

            self._cutoff = min(self._cutoff, int(self._n / 2))

            for i in range(self._cutoff):
                left, left_residuals = ols(np.arange(i), data[column_name][:i])
                right, right_residuals = ols(np.arange(i, self._cutoff), data[column_name][i:self._cutoff])

                err = ((i-1) / (self._cutoff-1) * rmse(left_residuals)) + ((self._cutoff-i) / (self._cutoff-1) * rmse(right_residuals))
                
                self.lefts = self.lefts.append(left, ignore_index=True)
                self.rights = self.rights.append(right, ignore_index=True)

                self.error.append(err)

            self.error = np.array(self.error)
            self.error = self.error[~np.isnan(self.error)]

            self.current_knee = self.error.argmin() if self.error.size > 0 else 0
            print('CUR KNEE', self.current_knee)
            print('LAST KNEE', self._last_knee)
            print('CUTOFF', self._cutoff)

            if (self.current_knee >= self._last_knee or self.current_knee <= 10): break

            self._cutoff = self.current_knee * 2

        print(data.index[:self.current_knee])
        print('cutoff:', self.current_knee)


    def plot_loss(self, fpath):
        plt.figure()
        plt.plot(self.error)

        argmin = self.current_knee
        plt.axvline(x=argmin, color='red', linestyle='--')
        plt.axhline(y=self.error.min() if self.error.size > 0 else 0, color='red', linestyle='--')
        plt.savefig(f'{fpath}.png')


    def plot_cutoff(self, data, col_names, fpath, title):
        plt.figure()
        plt.rc('xtick', labelsize=8) #fontsize of the x tick labels
        
        for col_name in col_names: data[col_name][:self._cutoff].plot(logx=False, logy=False, alpha=.5 if col_name == 'levenshtein' else 1)

        argmin = self.current_knee

        plt.title(title)
        plt.xticks(rotation=-15)

        plt.plot(self.lefts.iloc[argmin].alpha_hat + self.lefts.iloc[argmin].beta_hat * np.arange(argmin))

        right = np.arange(argmin, self._cutoff)
        plt.plot(right, self.rights.iloc[argmin].alpha_hat + self.rights.iloc[argmin].beta_hat * right)

        plt.axvline(x=argmin, color='red', linestyle='--')
        plt.annotate(argmin, (argmin+1, .9), color='red')
        plt.legend()
        plt.savefig(f'{fpath}.png')