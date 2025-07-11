#!/usr/bin/env node

const http = require('http');

const checkHealth = () => {
  const options = {
    hostname: 'localhost',
    port: 3003,
    path: '/',
    method: 'GET',
    timeout: 5000,
  };

  const req = http.request(options, (res) => {
    if (res.statusCode === 200 || res.statusCode === 304) {
      console.log('✅ Frontend is healthy');
      process.exit(0);
    } else {
      console.log(`❌ Frontend returned status ${res.statusCode}`);
      process.exit(1);
    }
  });

  req.on('error', (err) => {
    console.log(`❌ Frontend is down: ${err.message}`);
    process.exit(1);
  });

  req.on('timeout', () => {
    console.log('❌ Frontend health check timed out');
    req.destroy();
    process.exit(1);
  });

  req.end();
};

checkHealth();
