import functools

def replace_dummies(string, *args, **kwargs):
    """
    Replace DUMMY_MAPCALC_STRINGS (see SplitWindowLST class for it)
    with input maps ti, tj (here: t10, t11).

    - in_ti and in_tj are the "input" strings, for example:
    in_ti = 'Input_T10'  and  in_tj = 'Input_T11'

    - out_ti and out_tj are the output strings which correspond to map
    names, user-fed or in-between temporary maps, for example:
    out_ti = t10  and  out_tj = t11

    or

    out_ti = tmp_ti_mean  and  out_tj = tmp_ti_mean

    (Idea sourced from: <http://stackoverflow.com/a/9479972/1172302>)
    """
    inout = set(['instring', 'outstring'])
    # if inout.issubset(set(kwargs)):  # alternative
    if inout == set(kwargs):
        instring = kwargs.get('instring', 'None')
        outstring = kwargs.get('outstring', 'None')

        # end comma important!
        replacements = (str(instring), str(outstring)),

    in_tij_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj'])

    if in_tij_out == set(kwargs):
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')

        replacements = (in_ti, str(out_ti)), \
                       (in_tj, str(out_tj))

    in_tijm_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj',
                       'in_tim', 'out_tim', 'in_tjm', 'out_tjm'])

    if in_tijm_out == set(kwargs):
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')
        in_tim = kwargs.get('in_tim', 'None')
        out_tim = kwargs.get('out_tim', 'None')
        in_tjm = kwargs.get('in_tjm', 'None')
        out_tjm = kwargs.get('out_tjm', 'None')

        replacements = (in_ti, str(out_ti)), \
                       (in_tj, str(out_tj)), \
                       (in_tim, str(out_tim)), \
                       (in_tjm, str(out_tjm))

    in_cwv_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj', 'in_cwv',
                      'out_cwv'])

    if in_cwv_out == set(kwargs):
        in_cwv = kwargs.get('in_cwv', 'None')
        out_cwv = kwargs.get('out_cwv', 'None')
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')

        replacements = (in_ti, str(out_ti)), \
                       (in_tj, str(out_tj)), \
                       (in_cwv, str(out_cwv))

    in_lst_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj', 'in_cwv',
                      'out_cwv', 'in_avg_lse', 'out_avg_lse', 'in_delta_lse',
                      'out_delta_lse'])

    if in_lst_out == set(kwargs):
        in_cwv = kwargs.get('in_cwv', 'None')
        out_cwv = kwargs.get('out_cwv', 'None')
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')
        in_avg_lse = kwargs.get('in_avg_lse', 'None')
        out_avg_lse = kwargs.get('out_avg_lse', 'None')
        in_delta_lse = kwargs.get('in_delta_lse', 'None')
        out_delta_lse = kwargs.get('out_delta_lse', 'None')

        replacements = (in_ti, str(out_ti)), \
                       (in_tj, str(out_tj)), \
                       (in_cwv, str(out_cwv)), \
                       (in_avg_lse, str(out_avg_lse)), \
                       (in_delta_lse, str(out_delta_lse))

    return functools.reduce(lambda alpha, omega: alpha.replace(*omega),
                  replacements, string)
