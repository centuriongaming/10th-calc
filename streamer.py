import random
import pandas as pd
import plotly.express as px
from collections import defaultdict
import streamlit as st
import math
import numpy as np

st.set_page_config(page_title='Unitcrunch', layout='wide')

tag_names = ['Rapid Fire', 'Twin Linked', 'Torrent', 'Lance', 'Blast', 'Melta', 'Heavy', 'Hazardous',
             'Devastating Wounds', 'Anti-', 'Sustained Hits', 'Extra Attacks']
weapon_tag_enabled = [False for x in range(len(tag_names))]
weapon_tags = pd.DataFrame({
    'Weapon Tags': tag_names,
    'Enabled?': weapon_tag_enabled
})

keyword_names = ['Infantry', 'Vehicle', 'Mounted', 'Monster', 'Psyker']
anti_keyword_names = keyword_names
keyword_enabled = [False for x in range(len(keyword_names))]
anti_keyword_enabled = [False for x in range(len(anti_keyword_names))]
keywords = pd.DataFrame({
    'Keywords': keyword_names,
    'Enabled?': keyword_enabled
})
anti_keywords = pd.DataFrame({
    'Anti-Keywords': anti_keyword_names,
    'Is Anti-X?': anti_keyword_enabled
})
attacker, data, defender = st.columns([0.2, 0.6, 0.2])
with attacker:
    # TODO: Precision
    st.header('Attacker')
    st.text_input('Attacks',
                  placeholder='e.g. 2D6',
                  value='10',
                  key='attacks')
    st.number_input('WS/BS', step=1, format='%d', key='skill', value=3, min_value=2, max_value=6)
    st.number_input('Strength', step=1, format='%d', key='strength')
    st.number_input('AP', step=1, format='%d', key='ap')
    st.text_input('Damage', placeholder='e.g. 2D6', key='damage')
    st.checkbox('Half Range?', key='is_half')
    if st.checkbox('Rapid Fire?', key='is_rf'):
        st.text_input('Rapid Fire Value:', placeholder='e.g. 2D6', key='rfv')
    st.checkbox('Twin Linked?', key='is_tw')
    st.checkbox('Torrent?', key='is_torr')
    st.checkbox('Lethal Hits?', key='is_lh')
    if st.checkbox('Lance?', key='is_lance'):
        st.checkbox('Charged?', key='is_charge')
    st.checkbox('Blast?', key='is_blast')
    if st.checkbox('Melta?', key='is_melta'):
        st.text_input('Melta Value:', placeholder='e.g. 2D6', key='meltav')
    if st.checkbox('Heavy?', key='is_heavy'):
        st.checkbox('Remained Stationary?', key='is_rs')
    st.checkbox('Devastating Wounds?', key='is_dw')
    if st.checkbox('Sustained Hits?', key='is_sh'):
        st.text_input('Sustained Hits Value', placeholder='e.g. 2D6', key='shv')
    if st.checkbox('Anti-?', key='is_anti'):
        anti_keyword_df = st.data_editor(anti_keywords,
                                         column_config={
                                             "Is Anti-X?": st.column_config.CheckboxColumn(
                                                 "Is Anti?",
                                                 default=False,
                                                 width='small'
                                             )
                                         },
                                         disabled=['Keyword Names'],
                                         hide_index=True,
                                         key='antid')
        st.number_input('Anti- Value', format='%d', value=3, min_value=2, max_value=6, key='antiv')
with data:
    st.header('Data')
    summary_page, hits_dealt, wounds_dealt, unsaved_wounds, damage_dealt = st.tabs([
        "Summary", "Hits", "Wounds Dealt", "Unsaved Wounds", "Damage Dealt"
    ])
with defender:
    # TODO: Stealth
    st.header('Defender')
    keyword_df = st.data_editor(keywords,
                                column_config={
                                    "Enabled?": st.column_config.CheckboxColumn(
                                        "Enabled?",
                                        default=False,
                                        width='small'
                                    )
                                },
                                disabled=['Keyword Names'],
                                hide_index=True,
                                key='keywordd')
    st.number_input('Number of Models', step=1, format='%d', key='num_models')
    st.number_input('Wounds', step=1, format='%d', key='wounds')
    st.number_input('Toughness', step=1, format='%d', key='toughness')
    st.number_input('Save', step=1, format='%d', key='save')
    if st.checkbox('Invuln?', key='is_invuln'):
        st.number_input('Invuln Value', step=1, format='%d', key='invulnv')
    if st.checkbox('Feel No Pain?', key='is_fnp'):
        st.number_input('Feel No Pain Value', step=1, format='%d', key='fnpv')
    if st.checkbox('Attached Character?', key='is_attch'):
        st.number_input('Character Wounds', step=1, format='%d', key='chw')
        st.number_input('Character Save', step=1, format='%d', key='chs')
        if st.checkbox('Character Invuln?', key='is_cinvuln'):
            st.number_input('Character Invuln', step=1, format='%d', key='chi')
        if st.checkbox('Character Feel No Pain?', key='is_cfnp'):
            st.number_input('Character Feel No Pain Value', step=1, format='%d', key='cfnp')


def text_to_number(text):
    has_d = text.find('D')
    has_plus = text.find('+')
    if has_d >= 0:
        if has_d == 0:
            text = '1' + text
            has_d = 1
        number_of_rolls = int(text[0])
        die_to_roll = int(text[has_d + 1:has_plus] if has_plus > 0 else text[has_d + 1:])
        res = np.sum(np.random.randint(low=1, high=die_to_roll + 1, size=number_of_rolls))
        res = res + int(text[has_plus + 1:]) if has_plus > 0 else res
        return res
    else:
        return int(text)


def to_hit():
    # Calc number of attacks
    num_attacks = text_to_number(st.session_state.attacks)
    if st.session_state.is_rf:
        if st.session_state.is_half:
            num_rapid = text_to_number(st.session_state.rfv)
            num_attacks = num_attacks + num_rapid
    if st.session_state.is_blast:
        num_models = int(st.session_state.num_models)
        blast_attacks = math.floor(num_models / 5)
        num_attacks = num_attacks + blast_attacks

    hit_rolls = np.random.randint(low=1, high=7, size=num_attacks)
    if st.session_state.is_torr:
        return hit_rolls
    not_abject_failure_cond = hit_rolls != 1
    hit_rolls = np.extract(not_abject_failure_cond, hit_rolls)
    successes = np.array([])
    abject_success_cond = hit_rolls == 6
    not_abject_success_cond = hit_rolls != 6
    successes = np.append(successes, np.extract(abject_success_cond, hit_rolls))
    hit_rolls = np.extract(not_abject_success_cond, hit_rolls)
    skill = int(st.session_state.skill)
    if st.session_state.is_heavy and st.session_state.is_rs:
        skill = skill + 1
    hit_cond = hit_rolls >= skill
    successes = np.append(successes, np.extract(hit_cond, hit_rolls))
    return successes


def strength_v_toughness(strength, toughness):
    at_least_to_wound = int
    if strength >= toughness * 2:
        at_least_to_wound = 2
    elif strength > toughness:
        at_least_to_wound = 3
    elif strength == toughness:
        at_least_to_wound = 4
    elif strength < toughness and not strength <= toughness / 2:
        at_least_to_wound = 5
    elif strength <= toughness / 2:
        at_least_to_wound = 6
    return at_least_to_wound


def anti_corresponds():
    # keyword_df, anti_keyword_df
    key_df = keyword_df.set_index('Keywords').join(anti_keyword_df.set_index('Anti-Keywords'))
    check = (key_df['Enabled?'] & key_df['Is Anti-X?']).any()
    return check


def to_wound(hits):
    strength = st.session_state.strength
    toughness = st.session_state.toughness
    at_least_to_wound = strength_v_toughness(strength, toughness)
    wound_rolls = np.random.randint(low=1, high=7, size=len(hits))
    if st.session_state.is_lh:
        return wound_rolls
    successes = np.array([])
    failures = np.array([])

    abject_success_val = 6
    if st.session_state.is_anti and anti_corresponds():
        abject_success_val = st.session_state.antiv
    abject_success_cond = wound_rolls == abject_success_val
    not_abject_success_cond = wound_rolls != abject_success_val
    successes = np.append(successes, np.extract(abject_success_cond, wound_rolls))
    wound_rolls = np.extract(not_abject_success_cond, wound_rolls)

    not_abject_failure_cond = wound_rolls != 1
    abject_failure_cond = wound_rolls == 1
    failures = np.append(failures, np.extract(abject_failure_cond, wound_rolls))
    wound_rolls = np.extract(not_abject_failure_cond, wound_rolls)
    if st.session_state.is_lance:
        at_least_to_wound = at_least_to_wound + 1
    wound_cond = wound_rolls >= at_least_to_wound
    fail_to_wound = wound_cond < at_least_to_wound
    failures = np.append(failures, np.extract(fail_to_wound, wound_rolls))
    successes = np.append(successes, np.extract(wound_cond, wound_rolls))
    if st.session_state.is_tw:
        new_rolls = np.random.randint(low=1, high=7, size=len(failures))
        successes = np.append(successes, np.extract(abject_success_cond, new_rolls))
        new_rolls = np.extract(not_abject_success_cond, new_rolls)
        successes = np.append(successes, np.extract(wound_cond, new_rolls))
    return successes, failures


def feel_no_pain(total_damage, is_fnp, fnpv):
    if is_fnp:
        rolls = np.random.randint(low=1, high=7, size=total_damage)
        success_cond = rolls > fnpv
        successes = np.extract(success_cond, rolls)
        damage = np.ones_like(successes)
        return np.sum(damage)
    else:
        return total_damage


def check_if_point_taken(is_character):
    if not st.session_state.is_dw:
        save = st.session_state.chs if is_character else st.session_state.save
        if is_character and st.session_state.is_chinvuln:
            invuln = st.session_state.chi
        elif not is_character and st.session_state.is_invuln:
            invuln = st.session_state.invulnv
        else:
            invuln = 7
        save = save + st.session_state.ap
        if invuln <= save:
            saving_value = invuln
        else:
            saving_value = save
        roll = random.randint(1, 6)
        if roll >= saving_value:
            return 0
    if is_character and st.session_state.is_cfnp:
        fnp = st.session_state.cfnp
    elif not is_character and st.session_state.is_fnp:
        fnp = st.session_state.fnpv
    else:
        fnp = 7
    roll = random.randint(1, 6)
    if roll >= fnp:
        return 0
    return 1


def damage(wounds):
    damagec = text_to_number(st.session_state.damage) * len(wounds)
    character_is_alive = True
    if st.session_state.is_melta and st.session_state.is_half:
        damagec = damagec + text_to_number(st.session_state.meltav)
    models = np.full(st.session_state.num_models, st.session_state.wounds)
    untaken_damage = np.full(damagec, 1)
    taken_damage = np.array([])
    while len(untaken_damage) > 0:
        point = check_if_point_taken(False)
        models[0] = models[0] - point
        untaken_damage = untaken_damage[1:]
        taken_damage = np.append(taken_damage, point)
        if models[0] == 0:
            models = models[1:]
        if len(models) == 0:
            break
    while len(untaken_damage) > 0 and st.session_state.is_attch:
        character = np.array([st.session_state.chw])
        point = check_if_point_taken(True)
        character[0] = character[0] - point
        untaken_damage = untaken_damage[1:]
        taken_damage = np.append(taken_damage, point)
        if models[0] == 0:
            character_is_alive = False
            break
    return len(models), character_is_alive, np.sum(taken_damage)


def generate_data():
    MONTE_CARLO_SIM_NUM = 1000
    i = 0
    average_hits = {}
    average_unsaved_wounds = {}
    average_wounds_dealt = {}
    average_damage = {}
    average_models_slain = {}
    killed_character = {}
    while i < MONTE_CARLO_SIM_NUM:
        hits = to_hit()
        average_hits[len(hits)] = average_hits.get(len(hits), 0) + 1
        unsaved_wounds_list, saved_wounds = to_wound(hits)
        average_unsaved_wounds[len(unsaved_wounds_list)] = average_unsaved_wounds.get(len(hits), 0) + 1
        average_wounds_dealt[len(unsaved_wounds_list) + len(saved_wounds)] = \
            average_wounds_dealt.get(len(unsaved_wounds_list) + len(saved_wounds), 0) + 1
        d = damage(average_unsaved_wounds)
        average_models_slain[d[0]] = average_models_slain.get(d[0], 0) + 1
        average_damage[d[2]] = average_damage.get(d[2], 0) + 1
        killed_character[d[1]] = killed_character.get(d[1], 0) + 1
        i = i + 1
    weighted_slain = sum(key * value for key, value in average_models_slain.items())
    progress = weighted_slain / sum(average_models_slain.values())
    chances = sum(value for key, value in average_models_slain.items() if key >= progress) / sum(average_models_slain.values())
    with data:
        with summary_page:
            st.subheader(f'Models Slain: {round(progress)}')
            st.progress(round(progress / st.session_state.num_models * 100))
            chance_text = "Chance of %d or better: %d Percent" % (round(progress), chances*100)
            st.text(chance_text)
            percentages = [(value / sum(average_models_slain.values()))
                           * 100 for value in average_models_slain.values()]
            models_slain_df = pd.DataFrame({'Models Slain': list(average_models_slain.keys()),
                                            '%': percentages}).sort_values('Models Slain')
            fig = px.bar(models_slain_df, x='Models Slain', y='%')
            fig.update_xaxes(type='category')
            st.plotly_chart(fig)
        with hits_dealt:
            percentages = [(value / sum(average_hits.values()))
                           * 100 for value in average_hits.values()]
            models_slain_df = pd.DataFrame({'Hits': list(average_hits.keys()),
                                            '%': percentages}).sort_values('Hits')
            fig = px.bar(models_slain_df, x='Hits', y='%')
            fig.update_xaxes(type='category')
            st.plotly_chart(fig)
        with wounds_dealt:
            percentages = [(value / sum(average_wounds_dealt.values()))
                           * 100 for value in average_wounds_dealt.values()]
            models_slain_df = pd.DataFrame({'Wounds': list(average_wounds_dealt.keys()),
                                            '%': percentages}).sort_values('Wounds')
            fig = px.bar(models_slain_df, x='Wounds', y='%')
            fig.update_xaxes(type='category')
            st.plotly_chart(fig)
        with unsaved_wounds:
            percentages = [(value / sum(average_unsaved_wounds.values()))
                           * 100 for value in average_unsaved_wounds.values()]
            models_slain_df = pd.DataFrame({'Wounds': list(average_unsaved_wounds.keys()),
                                            '%': percentages}).sort_values('Wounds')
            fig = px.bar(models_slain_df, x='Wounds', y='%')
            fig.update_xaxes(type='category')
            st.plotly_chart(fig)
        with damage_dealt:
            percentages = [(value / sum(average_damage.values()))
                           * 100 for value in average_damage.values()]
            models_slain_df = pd.DataFrame({'Wounds': list(average_damage.keys()),
                                            '%': percentages}).sort_values('Wounds')
            fig = px.bar(models_slain_df, x='Wounds', y='%')
            fig.update_xaxes(type='category')
            st.plotly_chart(fig)
    # st.write(hits)
    # st.write(wounds)
    # st.write(d)


st.button('Submit', use_container_width=True, on_click=generate_data)
