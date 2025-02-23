#%%
import numpy as np 
import bokeh.io 
import seaborn as sns
import bokeh.plotting 
import bokeh.layouts
import bokeh.models
import growth.model
import growth.viz 
colors, palette = growth.viz.bokeh_style()
const = growth.model.load_constants()
bokeh.io.output_file('../../figures/interactive/interactive_steadystate.html')

# ############################################################################## 
# CONSTANT DEFINITIONS
# ############################################################################## 
phi_O = 0.55
phiRb_range = np.linspace(0.001, 1 - phi_O-0.001, 500)
gamma_max = const['gamma_max']
nu_max = 4.5 
nu_start, nu_end, nu_step = [0.01, 20, 0.1]
nu_range = np.arange(nu_start, nu_end, nu_step)
Kd_cpc = const['Kd_cpc']
ind = np.where(np.round(nu_range, decimals=1) == nu_max)[0][0]
cmap = sns.color_palette('crest', n_colors=len(nu_range) + 1).as_hex()

# ############################################################################## 
# INITIALIZATION    
# ############################################################################## 
growth_rate = growth.model.steady_state_growth_rate(gamma_max, phiRb_range, nu_range[ind], Kd_cpc, phi_O)
cpc = growth.model.steady_state_precursors(gamma_max, phiRb_range, nu_range[ind], Kd_cpc, phi_O)
gamma = growth.model.steady_state_gamma(gamma_max, phiRb_range, nu_range[ind], Kd_cpc, phi_O)
source = bokeh.models.ColumnDataSource({'phiRb': [phiRb_range], 
                                        'lam':[growth_rate / growth_rate.max()],
                                        'cpc':[cpc / Kd_cpc],
                                        'gamma': [gamma / gamma_max],
                                        'color': [cmap[ind]]})
# ############################################################################## 
# WIDGET DEFINITIONS
# ############################################################################## 
phiO_slider = bokeh.models.Slider(start=0, end=0.75, step=0.001, value=phi_O,
                    title='allocation to other proteins',
                    bar_color=colors['light_black'])
gamma_slider = bokeh.models.Slider(start=0.001, end=25, step=0.001, value=20,
                    title='maximum translation speed [AA / s]',
                    bar_color = colors['primary_green'])
nu_slider = bokeh.models.Slider(start=nu_start, end=nu_end, step=nu_step, value=nu_max,
                    title='maximal metabolic rate [inv. hr]',
                    bar_color=cmap[ind])
Kd_cpc_slider = bokeh.models.Slider(start=-4, end=-0.0001, step=0.001, value=np.log10(Kd_cpc),
                    title='log\u2081\u2080 precursor Michaelis-Menten constant',
                    bar_color=colors['light_black'])

# ############################################################################## 
# CANVAS DEFINITIONS
# ############################################################################## 

growth_axis = bokeh.plotting.figure(width=300, height=300, 
                                    x_axis_label='allocation towards ribosomes',
                                    y_axis_label=r"$$\lambda / \lambda_{max}$$",
                                    title='relative steady state growth rate',
                                    x_range=[0, 1],
                                    y_range= [0, 1.1])
precursor_axis = bokeh.plotting.figure(width=300, height=300,
                                    x_axis_label='allocation towards ribosomes',
                                    y_axis_label=r"$$c_{pc} / K_M^{(c_{pc})}$$",
                                    title='relative steady state precursor concentration',
                                    y_axis_type='log',
                                    x_range = [0, 1])
gamma_axis = bokeh.plotting.figure(width=300, height=300,
                                    x_axis_label='allocation towards ribosomes',
                                    y_axis_label=r"$$v_{tl} / v_{tl}^{max}$$",
                                    title='relative steady state translation speed',
                                    x_range = [0, 1],
                                    y_range = [0, 1.1])

# ############################################################################## 
# GLYPH DEFINITIONS
# ############################################################################## 
# Using multi_line such that color field can be provided as a source kdim
growth_axis.multi_line(xs='phiRb', ys='lam', line_width=2, line_color='color', 
                        source=source)
precursor_axis.multi_line(xs='phiRb', ys='cpc', line_width=2, line_color='color', 
                        source=source)
gamma_axis.multi_line(xs='phiRb', ys='gamma', line_width=2, line_color='color', 
                    source=source)

# ############################################################################## 
# CALLBACK DEFINITIONS
# ############################################################################## 
args = {'gamma_slider': gamma_slider,
        'nu_slider': nu_slider,
        'Kd_cpc_slider': Kd_cpc_slider,
        'phiO_slider': phiO_slider,
        'source': source,
        'colorArray': cmap}
callback = growth.viz.load_js(['./interactive_steadystate.js', './functions.js'],
                        args=args)
for s in [gamma_slider, nu_slider, Kd_cpc_slider, phiO_slider]:
    s.js_on_change('value', callback)

# ############################################################################## 
# LAYOUT DEFINITION
# ############################################################################## 
sliders_1 = bokeh.layouts.column(gamma_slider, nu_slider)
sliders_2 = bokeh.layouts.column(phiO_slider, Kd_cpc_slider)
sliders = bokeh.layouts.Row(sliders_1, sliders_2)
plots = bokeh.layouts.Row(precursor_axis, gamma_axis, growth_axis)

layout = bokeh.layouts.Column(sliders, plots)
bokeh.io.save(layout)
# %%
