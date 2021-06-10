import datetime
import tabulate, copy, time, requests, os
from operator import itemgetter
import telegram

channel = '-'   #Enter Telegram channel/chat ID
bot = telegram.Bot(token='')    #Enter Telegram bot token

#Change the below variables according to your needs
minimum_slots = 1
min_age_booking = 24
fee_type = ['Free']           #Free or Paid or Both
CALENDAR_URL_DISTRICT = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={0}&date={1}"
start_date = 1
vaccine = 'covishield'   #vaccine choice
pincode_range = range(400055, 400104)   #pincode range for centers
dose = 1   #Dose number
dose_str = 'available_capacity_dose1' if dose == 1 else 'available_capacity_dose2'


def display_table(dict_list):
    """
    This function
        1. Takes a list of dictionary
        2. Add an Index column, and
        3. Displays the data in tabular format
    """
    try:
        header = ['idx'] + list(dict_list[0].keys())
        rows = [[idx + 1] + list(x.values()) for idx, x in enumerate(dict_list)]
        print(tabulate.tabulate(rows, header, tablefmt='grid'))
    except IndexError:
        print("No table to show")


base_request_header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    'origin': 'https://selfregistration.cowin.gov.in/',
    'referer': 'https://selfregistration.cowin.gov.in/'
}

request_header = copy.deepcopy(base_request_header)

if isinstance(start_date, int) and start_date == 2:
    start_date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%d-%m-%Y")
elif isinstance(start_date, int) and start_date == 1:
    start_date = datetime.datetime.today().strftime("%d-%m-%Y")

base_url = CALENDAR_URL_DISTRICT

msg = ''
while True:
    try:
        msg = ''
        resp = requests.get(base_url.format(395, start_date), headers=request_header)
        resp = resp.json()
        options = []
        acenters = []
        if len(resp['centers']) >= 0:
            for center in resp['centers']:
                for session in center['sessions']:
                    if (session['min_age_limit'] <= min_age_booking) \
                            and (center['fee_type'] in fee_type) \
                            and (center['pincode'] in pincode_range):

                        availability = session[dose_str]

                        acenter = {
                            'name': center['name'],
                            'pincode': center['pincode'],
                            'center_id': center['center_id'],
                            'available': availability,
                            'date': session['date'],
                            # 'session_id': session['session_id'],
                            'vaccine': session['vaccine'],
                            'slots': session['slots']

                        }
                        acenters.append(acenter)
                        if (availability >= minimum_slots) \
                                and (session['vaccine'].lower() == vaccine):
                            out = {
                                'name': center['name'],
                                'district': center['district_name'],
                                'pincode': center['pincode'],
                                'center_id': center['center_id'],
                                'available': availability,
                                'date': session['date'],
                                'slots': session['slots'],
                                'session_id': session['session_id'],
                                'vaccine': session['vaccine'],
                            }
                            msg = msg + f"\n{center['name']} \nVaccine: {session['vaccine']} \nOn {session['date']} \nSeats Availabe: {session['available_capacity']} \nPincode {center['pincode']}\n"
                            options.append(out)
        print(f"Centers for {min_age_booking}+ age:")

        acenters = sorted(acenters, key=itemgetter('pincode'))
        print("Showing all centers in your area (including full booked): ")
        display_table(acenters)
        print("Showing all viable options: ")
        display_table(options)
        if len(options) > 0:
            bot.sendMessage(channel, msg[:4000])
            os.system('play -n synth 1  sin 300')
        print(datetime.datetime.now().strftime('%H:%M:%S'))
        time.sleep(10)
    except Exception as error:
        print(f'\nSome error \nDetails: {error}')
        time.sleep(10)
