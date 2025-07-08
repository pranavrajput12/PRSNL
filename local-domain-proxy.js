const http = require('http');
const httpProxy = require('http-proxy');

// Create proxy servers for different projects
const proxies = {
  'prsnl.test': 'http://localhost:3002',
  'api.prsnl.test': 'http://localhost:8000',
  'prsnl.dev': 'http://localhost:3002',
  'api.prsnl.dev': 'http://localhost:8000'
};

const proxy = httpProxy.createProxyServer({});

const server = http.createServer((req, res) => {
  const host = req.headers.host;
  const target = proxies[host];
  
  if (target) {
    proxy.web(req, res, { target });
  } else {
    res.writeHead(404);
    res.end('Domain not configured');
  }
});

proxy.on('error', (err, req, res) => {
  res.writeHead(502);
  res.end('Proxy error');
});

server.listen(80, () => {
  console.log('Local domain proxy running on port 80');
  console.log('Available domains:');
  Object.keys(proxies).forEach(domain => {
    console.log(`  http://${domain} -> ${proxies[domain]}`);
  });
});