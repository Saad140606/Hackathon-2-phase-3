from src.config import settings
import os
print('Loaded settings.cohere_api_key:', settings.cohere_api_key)
print('Loaded settings.openai_api_key:', settings.openai_api_key)
try:
    import cohere
    print('cohere version:', getattr(cohere, '__version__', 'unknown'))
    key = os.environ.get('COHERE_API_KEY') or settings.cohere_api_key
    print('Effective COHERE_API_KEY present:', bool(key))
    client = cohere.Client(key)
    # Try a short generate call
    resp = client.generate(model=settings.cohere_model or 'xsmall', prompt='Say hello.', max_tokens=10)
    gens = getattr(resp, 'generations', None)
    if gens:
        print('Generation text:', gens[0].text[:200])
    else:
        print('No generations attribute; response type:', type(resp), 'repr:', resp)
except Exception as e:
    import traceback
    print('Cohere probe exception:')
    traceback.print_exc()
