UPDATE email_templates 
SET 
  subject = 'Your brain just got an upgrade 🧠',
  html_template = '<div style="font-family: -apple-system, BlinkMacSystemFont, ''Segoe UI'', Roboto, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <h2 style="color: #000;">Hey {{user_name}}!</h2>
  
  <p>Welcome to PRSNL - where "FYI" means "For Your Intelligence" 😉</p>
  
  <p><strong>Your second brain is warming up. Here''s what just happened:</strong></p>
  <ul style="list-style: none; padding: 0;">
    <li>✅ Neural pathways: Connected</li>
    <li>✅ Memory palace: Constructed</li>
    <li>✅ Knowledge cortex: Activated</li>
  </ul>
  
  <p><strong>Quick FYI - here''s how to feed your new brain:</strong></p>
  <ul style="margin: 20px 0;">
    <li>Capture anything → It learns your patterns</li>
    <li>Search everything → It remembers for you</li>
    <li>Connect the dots → It thinks with you</li>
  </ul>
  
  <p><strong>Ready to make it personal?</strong></p>
  <div style="margin: 30px 0;">
    <a href="{{app_link}}/capture" style="background-color: #dc143c; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-right: 10px; display: inline-block;">Start Capturing</a>
    <a href="{{app_link}}/features" style="background-color: #333; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-right: 10px; display: inline-block;">Explore Features</a>
    <a href="{{app_link}}/chat" style="background-color: #666; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Meet Your AI</a>
  </div>
  
  <p><strong>P.S.</strong> Your brain''s first meal? Try saving this email.<br>
  Just forward it to <a href="mailto:capture@prsnl.fyi">capture@prsnl.fyi</a> 🎯</p>
  
  <p style="margin-top: 40px; color: #666;">
    Neurally yours,<br>
    The PRSNL Team
  </p>
</div>',
  text_template = 'Hey {{user_name}}!

Welcome to PRSNL - where "FYI" means "For Your Intelligence" 😉

Your second brain is warming up. Here''s what just happened:
✅ Neural pathways: Connected
✅ Memory palace: Constructed  
✅ Knowledge cortex: Activated

Quick FYI - here''s how to feed your new brain:
- Capture anything → It learns your patterns
- Search everything → It remembers for you
- Connect the dots → It thinks with you

Ready to make it personal?
Start Capturing: {{app_link}}/capture
Explore Features: {{app_link}}/features
Meet Your AI: {{app_link}}/chat

P.S. Your brain''s first meal? Try saving this email. 
Just forward it to capture@prsnl.fyi 🎯

Neurally yours,
The PRSNL Team',
  updated_at = NOW()
WHERE name = 'welcome';