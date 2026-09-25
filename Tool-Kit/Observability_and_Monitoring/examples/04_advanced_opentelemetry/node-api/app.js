const express = require('express');
const axios = require('axios');
const app = express();

app.get('/buy', async (req, res) => {
  try {
    // OpenTelemetry auto-instrumentation will automatically intercept this Axios request
    // and inject the W3C Traceparent Header into the outgoing HTTP request!
    const response = await axios.get(process.env.PYTHON_BACKEND_URL + '/process_payment');
    res.send(`Payment status: ${response.data.status}`);
  } catch (err) {
    res.status(500).send("Error");
  }
});

app.listen(3000, () => console.log('Node API running'));
