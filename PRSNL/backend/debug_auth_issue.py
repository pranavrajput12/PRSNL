import asyncio
import asyncpg
from app.config import settings
from passlib.context import CryptContext

async def debug_auth():
    conn = await asyncpg.connect(settings.DATABASE_URL)
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    try:
        # Check user data
        user = await conn.fetchrow('SELECT * FROM users WHERE email = $1', 'test@example.com')
        if user:
            print('User found:')
            for key, value in user.items():
                if key != 'password_hash':
                    print(f'  {key}: {value}')
            print(f'  password_hash: {user["password_hash"][:20]}...')
            
            # Test password
            try:
                result = pwd_context.verify('testpassword123', user['password_hash'])
                print(f'\nPassword verification: {result}')
            except Exception as e:
                print(f'\nPassword verification error: {e}')
                
            # Check required fields
            print('\nRequired fields check:')
            required = ['id', 'email', 'first_name', 'last_name', 'is_active', 'is_verified', 'user_type', 'onboarding_completed']
            for field in required:
                print(f'  {field}: {field in user} - Value: {user.get(field)}')
                
            # Check for None values
            print('\nChecking for None values:')
            for key, value in user.items():
                if value is None:
                    print(f'  {key} is None!')
        else:
            print('User not found')
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_auth())