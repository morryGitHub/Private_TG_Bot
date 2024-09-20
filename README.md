<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>

<h1>Telegram Bot for Weather and Currency</h1>

<p>This is a Python-based Telegram bot that provides various utilities, including weather updates, exchange rates for currencies, and some additional features like sharing music resources and showing user information.</p>

<h2>Features</h2>
<ul>
    <li><strong>Weather Information</strong>: Get current weather details for any city using the OpenWeather API.</li>
    <li><strong>Currency Exchange Rates</strong>: Fetch live exchange rates from different sources (PrivatBank API and X-Rates) for major world currencies.</li>
    <li><strong>Music Resources</strong>: Share links to free music resources.</li>
    <li><strong>User Commands</strong>: Basic commands for starting, showing help, and providing user information.</li>
</ul>

<h2>Bot Setup</h2>

<h3>Step 1: Configure API Keys</h3>
<p>Replace the placeholders in the code with your actual API keys:</p>
<pre>
API_TG = 'YOUR_TELEGRAM_BOT_API_KEY'
API_FORECAST = 'YOUR_OPENWEATHER_API_KEY'
</pre>

<h3>Step 2: Run the Bot</h3>
<p>To run the bot, simply execute the following command in your terminal:</p>
<pre>python bot.py</pre>
<p>Once running, the bot will automatically respond to messages and commands sent by users.</p>

<h2>Example Usage</h2>
<ul>
    <li>To get weather information for a city, simply send the <code>/weather</code> command and provide a city name (e.g., "Tralee").</li>
    <li>To get exchange rates in UAH, use <code>/currency_uah</code>, or for other currencies, use <code>/currency</code> and select the desired option.</li>
</ul>

</body>
</html>
