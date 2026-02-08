import os
try:
    import cohere
    key = os.environ.get('COHERE_API_KEY')
    print('COHERE_API_KEY present:', bool(key))
    client = cohere.Client(key)
    resp = client.generate(model='xsmall', prompt='Say hello in one line.', max_tokens=20)
    gens = getattr(resp, 'generations', None)
    if gens:
        print('Generation sample:', gens[0].text[:200])
    else:
        print('No generations attribute; response:', resp)
except Exception as e:
    print('Cohere probe exception:', repr(e))
