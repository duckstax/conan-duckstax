# conan-cyberduckninja

## Conan Information

# How To Use

```commandline
conan create . 1.0.0a4@duckstax/stable -o:cxx_standard=17 -o:fPIC=True
conan upload goblin-engineer/1.0.0a4@duckstax/stable  -r duckstax --all
```

## For Users

Add the corresponding remote to your conan:

```bash
conan remote add duckstax http://conan.duckstax.com:9300
```
