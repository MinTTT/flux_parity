# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import growth.viz
import growth.model
import growth.integrate
import scipy.integrate
import seaborn as sns
import tqdm
const = growth.model.load_constants()
source_colors = growth.viz.load_markercolors()
colors, palette = growth.viz.matplotlib_style()


# Load the parameter sweep data
sweep = pd.read_csv('../data/flux_parity_parameter_sweep.csv')
sweep = sweep[sweep['nu_max'] == 4.5]
# Generate the heatmaps
phiRb_map = np.zeros(
    (len(sweep['tau'].unique()), len(sweep['kappa_max'].unique())))
i = 0
for g, d in sweep.groupby(['tau']):
    phiRb_map[i, :] = d['phiRb'].values
    i += 1

# Compute the optimal growth rate and normalize the map
opt_phiRb = growth.model.phiRb_optimal_allocation(const['gamma_max'],
                                                  sweep['nu_max'].values[0],
                                                  const['Kd_cpc'],
                                                  const['phi_O'])
norm_phiRb = phiRb_map - opt_phiRb

# Create the mesh for positioning of contours and labels
kappa_ind = np.arange(0, len(sweep['kappa_max'].unique()), 1)
tau_ind = np.arange(0, len(sweep['tau'].unique()), 1)
X, Y = np.meshgrid(kappa_ind, tau_ind)


# Compute over a range of nu max.
nu_range = np.linspace(0.5, 20, 200)
FPM_phiRb_range = []
for i, nu in enumerate(tqdm.tqdm(nu_range)):
    args = {'nu_max': nu,
            'gamma_max': const['gamma_max'],
            'Kd_TAA': const['Kd_TAA'],
            'Kd_TAA_star': const['Kd_TAA_star'],
            'tau': const['tau'],
            'kappa_max': const['kappa_max'],
            'phi_O': const['phi_O']}
    out = growth.integrate.equilibrate_FPM(args)
    FPM_phiRb_range.append(out[1]/out[0])

opt_phiRb_range = growth.model.phiRb_optimal_allocation(const['gamma_max'], nu_range,
                                                        const['Kd_cpc'], const['phi_O'])


# %%
# Generate the tent plots using the simple allocation
nu_max = 4.5
phiRb_range = np.linspace(0.001, 1 - const['phi_O'] - 0.001, 300)
opt_lam = growth.model.steady_state_growth_rate(const['gamma_max'], opt_phiRb,
                                                nu_max, const['Kd_cpc'], const['phi_O'])
flux_df = pd.DataFrame([])

time = 100
for i, phi in enumerate(tqdm.tqdm(phiRb_range)):
    # Equilibrate the flux-parity system
    args = {'nu_max': nu_max,
            'gamma_max': const['gamma_max'],
            'Kd_TAA': const['Kd_TAA'],
            'Kd_TAA_star': const['Kd_TAA_star'],
            'tau': const['tau'],
            'kappa_max': const['kappa_max'],
            'dynamic_phiRb': {'phiRb': phi},
            'phi_O': const['phi_O'],
            'phiRb': phi}
    out = growth.integrate.equilibrate_FPM(args, max_iter=100)
    gamma = const['gamma_max'] * out[-1] / (out[-1] + const['Kd_TAA_star'])
    nu = nu_max * out[-2] / (out[-2] + const['Kd_TAA'])
    metab_flux = nu * out[2]/out[0]
    trans_flux = gamma * out[1]/out[0]  # (1 + out[-1] + out[-2])
    _df = pd.DataFrame([[metab_flux, trans_flux]],
                       columns=['metab_flux', 'trans_flux'])
    _df['TAA'] = out[-2]
    _df['TAA_star'] = out[-1]
    _df['balance'] = out[-1] / out[-2]
    _df['phi_Rb'] = phi
    flux_df = pd.concat([flux_df, _df], sort=False)

# Find the flux parity optimum
args = {'nu_max': nu_max,
        'gamma_max': const['gamma_max'],
        'Kd_TAA': const['Kd_TAA'],
        'Kd_TAA_star': const['Kd_TAA_star'],
        'tau': const['tau'],
        'kappa_max': const['kappa_max'],
        'phi_O': const['phi_O']}

FPM_out = growth.integrate.equilibrate_FPM(args)
FPM_phiRb = FPM_out[1]/FPM_out[0]

# %%
fig, ax = plt.subplots(1, 3, figsize=(7, 2.25))
# Format the axes
ax[0].set_xlabel('allocation towards ribosomes\n$\phi_{Rb}$')
ax[0].set_ylabel(
    '$J_{tl}/\lambda_{max}$, $J_{Mb}/\lambda_{max}$'+'\nrelative flux ')
# Set axis limits
ax[1].set_xlabel('maximum metabolic rate [hr$^{-1}$]\n'+r'$\nu_{max}$')
ax[1].set_ylabel(
    r'$\phi_{Rb}^{(flux-parity)} - \phi_{Rb}^{(III)}$' + '\ndifference in allocation')
# # Add appropriate heatmap ticks and labels.
# inds = [[], []]
# labs = [[], []]
# for i, vals in enumerate([sweep['kappa_max'].unique(), sweep['tau'].unique()]):
#     for j in range(np.log10(vals.min()).astype(int), np.log10(vals.max()).astype(int)+1):
#         if j % 2 == 0:
#             _ind = np.where(np.round(np.log10(vals), decimals=1) == j)
#             inds[i].append(_ind[0][0])
#             _exp = int(j)
#             labs[i].append('10$^{%s}$' % _exp)

# ax[1].set_xticks(inds[0])
# ax[1].set_xticklabels(labs[0])
# ax[1].set_yticks(inds[1])
# ax[1].set_yticklabels(labs[1])

# Make flux diagrams
ax[0].plot(flux_df['phi_Rb'], flux_df['metab_flux'] / opt_lam,
           '-', color=colors['primary_purple'], lw=2.5)
ax[0].plot(flux_df['phi_Rb'], flux_df['trans_flux'] /
           opt_lam, '-', color=colors['primary_gold'], lw=1)
ax[0].vlines(FPM_phiRb, -0.01, 1.2, lw=1,
             color=colors['primary_red'], linestyle='--')

# Plot tRNA species
ax[1].plot(nu_range, FPM_phiRb_range-opt_phiRb_range,
           lw=1.5, color=colors['primary_red'])

# Plot the heatmap and contours
# cmap = sns.diverging_palette(220, 20, as_cmap=True)
# ax[1].imshow(norm_phiRb, cmap=cmap, origin='lower', vmin=-0.3, vmax=0.3)
# cont_color = ['black', 'black',
#               colors['primary_red'], 'black', 'black', 'black']
# locations = [(20, 90), (30, 75), (50, 70), (40, 60), (30, 45), (10, 10)]
# conts = ax[1].contour(X, Y, norm_phiRb, levels=[-0.1, -0.05, 0.0, 0.05, 0.1, 0.25],
#                       colors=cont_color)
# ax[1].clabel(conts, conts.levels, inline=True, colors=cont_color, fontsize=6,
#              manual=locations)  # , fmt=)lambda x: f'{x}' + r' $\times$ $\phi_{Rb}^{(III)}$')

ax[1].set_ylim([-0.1, 0.1])
ax[1].set_yticks([-0.1, -0.05, 0, 0.05, 0.1])
ax[2].axis('off')
plt.tight_layout()
plt.savefig('../figures/main_text/Fig2.2_FPM_plots.pdf', bbox_inches='tight')
# # %% Generate the heat maps
# #%%

# %%
