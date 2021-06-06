import datetime
import logging
import time
from copy import deepcopy

import numpy as np
import pandas as pd
import streamlit as st
from requests import get
from twilio.rest import Client

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="COWIN Slot Finder", layout="wide")

slots = None
states = None
districts = None
MAIN_URL = "https://cdn-api.co-vin.in/api"

watch = {}
auto_refresh = True
RENAMED_COLUMNS = {
    'date': 'Date',
    'dose1_avail': 'DOSE 1 slots',
    'does2_avail': 'DOSE 2 slots',
    'min_age_limit': 'Minimum Age Limit',
    'available_capacity': 'Available Capacity',
    'vaccine': 'Vaccine',
    'pincode': 'Pincode',
    'name': 'Hospital Name',
    'state_name': 'State',
    'district_name': 'District',
    'block_name': 'Block Name',
    'fee_type': 'Fees'
}


@st.cache
def filter_column(df, col, value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp


@st.cache
def filter_capacity(df, col, value):
    df_temp = deepcopy(df.loc[df[col] > value, :])
    return df_temp


def fetch_slots(district: str, date: str):
    print("fetching new slots")
    url = MAIN_URL + "/v2/appointment/sessions/public/calendarByDistrict"
    payload = {'district_id': district, 'date': date}
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': "en_US",

    }
    response = get(url=url, params=payload, headers=headers)
    if response.ok and ('centers' in response.json()) and len(response.json()['centers']):
        data = response.json()
        data_frame = pd.DataFrame.from_dict(data["centers"])
        df = data_frame.explode("sessions")
        df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
        df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
        df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
        df['dose1_avail'] = df.sessions.apply(lambda x: x['available_capacity_dose1'])
        df['does2_avail'] = df.sessions.apply(lambda x: x['available_capacity_dose2'])
        df['date'] = df.sessions.apply(lambda x: x['date'])
        return df[
            ["date", "dose1_avail", "does2_avail", "available_capacity", "vaccine", "min_age_limit", "pincode", "name",
             "block_name", "fee_type"]]
    else:
        None


@st.cache
def fetch_states():
    url = MAIN_URL + "/v2/admin/location/states"
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': "en_US"
    }
    response = get(url=url, headers=headers)
    if response.ok and ('states' in response.json()):
        data = response.json()
        return pd.DataFrame.from_dict(data["states"])
    else:
        None


@st.cache
def fetch_district(state: str):
    url = MAIN_URL + f"/v2/admin/location/districts/{state}"
    payload = {'state_id ': state}
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': "en_US"
    }
    response = get(url=url, params=payload, headers=headers)
    if response.ok and ('districts' in response.json()):
        data = response.json()
        return pd.DataFrame.from_dict(data["districts"])
    else:
        None


# Streamlit APP

st.text('''
When you enable or disable auto_refresh new data may take up to 5 seconds to reflect.
To Avoid unnecessary calls to the API or twilio select all your filter parameters, before
selecting auto refresh and twilio sender.
For example Select state > Select District > select your filter parameters > now enable auto-refresh and twilio sender
''')

states = fetch_states()

criteria_container = st.beta_container()
cri_col1, cri_col2, cri_col3 = criteria_container.beta_columns(3)

twi_account = ""
twi_token = ""
phone_numbers = ""
msg_service = ""
last_notified = datetime.datetime.now() - datetime.timedelta(minutes = 6)
if auto_refresh is True:
    twilio_container = st.beta_container()
    twi_col1, twi_col2, twi_col3, twi_col4, twi_col5 = twilio_container.beta_columns(5)
    twi_account = twi_col1.text_input("Twilio Account Id", help="Twilio Account ID", value="")
    twi_token = twi_col2.text_input("Twilio Api token", help="Twilio Api token", value="")
    twi_service = twi_col4.text_input("From Messaging Service SID", value="")
    twi_send = twi_col5.checkbox("Enable Twilio sender")
    phone_numbers = twi_col3.text_input("Phone Numbers(10digit)", help="Separate multiple with commas", value="")
if states is not None:
    state_options = states["state_name"].tolist()
    state_ids = states["state_id"].tolist()
    dic_states = dict(zip(state_ids, state_options))
    selected_state = cri_col1.selectbox("Select State", state_ids, index=0, format_func=lambda x: dic_states[x])
    districts = fetch_district(selected_state)
else:
    st.error("unable to fetch states")
if districts is not None:
    district_options = districts["district_name"].tolist()
    district_ids = districts["district_id"].tolist()
    dic_districts = dict(zip(district_ids, district_options))
    selected_district = cri_col2.selectbox("Select District", district_ids, index=0, format_func=lambda x: dic_districts[x])
    date = datetime.date.today().strftime("%d-%m-%Y")
    slots = fetch_slots(selected_district, date)
else:
    st.error("unable to fetch districts")

if selected_state != "" and selected_district != "":
    auto_refresh = cri_col3.checkbox("Auto refresh", help="Refresh data every 5 seconds")
if slots is not None and len(slots):
    slots.drop_duplicates(inplace=True)
    slots.rename(columns=RENAMED_COLUMNS, inplace=True)
    cri_col1, cri_col2, cri_col3, col4, col5, col6 = st.beta_columns(6)
    with cri_col1:
        valid_pincodes = list(np.unique(slots["Pincode"].values))
        watch["pincode_inp"] = st.selectbox('Select Pincode', [""] + valid_pincodes)
        if watch["pincode_inp"] != "":
            slots = filter_column(slots, "Pincode", watch["pincode_inp"])

    with cri_col2:
        valid_age = [18, 45]
        watch["age_inp"] = st.selectbox('Select Minimum Age', [""] + valid_age)
        if watch["age_inp"] != "":
            slots = filter_column(slots, "Minimum Age Limit", watch["age_inp"])

    with cri_col3:
        valid_payments = ["Free", "Paid"]
        watch["pay_inp"] = st.selectbox('Select Free or Paid', [""] + valid_payments)
        if watch["pay_inp"] != "":
            slots = filter_column(slots, "Fees", watch["pay_inp"])

    with col4:
        valid_capacity = ["Available"]
        watch["cap_inp"] = st.selectbox('Select Availablilty', [""] + valid_capacity)
        if watch["cap_inp"] != "":
            slots = filter_capacity(slots, "Available Capacity", 0)

    with col5:
        valid_vaccines = ["COVISHIELD", "COVAXIN"]
        watch["vaccine_inp"] = st.selectbox('Select Vaccine', [""] + valid_vaccines)
        if watch["vaccine_inp"] != "":
            slots = filter_column(slots, "Vaccine", watch["vaccine_inp"])

    with col6:
        avail_dose = ["DOSE 1 slots", "DOSE 2 slots"]
        watch["vaccine_inp"] = st.selectbox('Select Dose', [""] + avail_dose)
        if watch["vaccine_inp"] != "":
            slots = filter_capacity(slots, watch["vaccine_inp"], 0)
    data_container = st.beta_container()
    data_container.table(slots)
    twilio_send_limit = datetime.datetime.now() - datetime.timedelta(minutes = 5)
    print(last_notified < twilio_send_limit)
    if len(slots) > 0 and (twi_send is True and twi_account != "" and twi_token != "" and twi_service != "" and (last_notified is None or last_notified < twilio_send_limit)):
        last_notified = datetime.datetime.now()
        account = twi_account
        token = twi_token
        client = Client(account, token, region='sg1')
        for number in phone_numbers.split(","):
            client.messages.create(
                messaging_service_sid=twi_service,
                to=f"+91{number}",
                body=f"slots available in {dic_states[selected_state]} at {dic_districts[selected_district]} with params {watch}"
            )


else:
    st.error("Unable to fetch data or No Slots available, may be try later")
while auto_refresh is True:
    print("refreshing...")
    st.empty()
    time.sleep(5)