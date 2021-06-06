# Cowin Slot availability checker and alerts
IMPORTANT: This project uses publicly available API's via APISetu. It doesn't book slots for you.
By default the rate limit set by the government is 100 calls per minute per IP.
![Screenshot](./img.jpg?raw=true)
## Usage
Requirements
 * Python 3.7 or above
 * conda (optional)
 
```bash
# in your terminal, command prompt or powershell
git clone https://github.com/anaganisk/cowin-slot-availability-alerts
cd cowin-slot-availability-alerts
# you can either activate your new conda or venv environment here or continue  if not required (optional)
pip install -r requirements.txt
streamlit run main.py
```

Tips:
* When you enable or disable auto_refresh new data may take up to 5 seconds to reflect.
To Avoid unnecessary calls to the API or twilio select all your filter parameters, before
selecting auto refresh and twilio sender.
**For example Select state > Select District > select your filter parameters > now enable auto-refresh and twilio sende**r
  
* Do select all you relevant filters including dosage to retrieve accurate results.

## License
    Copyright (C) <2021>  <Sai Kiran Anagani>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

This is a complete rewrite of https://github.com/bhattbhavesh91/cowin-vaccination-slot-availability and adds Auto refresh, also Twilio notifications via sms to fit my needs.