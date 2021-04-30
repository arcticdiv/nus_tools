# nus_tools
Framework for interfacing with eShop servers and processing data

---

## Install
Requires Python `>= 3.7`
```
pip install git+https://github.com/arcticdiv/nus_tools
```

## Usage
docs: soon™

### Certificates/Keys
There are a few certificates/keys required for some operations:
  - TLS client certificate (`CTR/WIIU Common Prod`)
    - required for accessing some eShop servers, notably `ninja` and some `ccs` servers
    - [link](https://github.com/larsenv/NintendoCerts/tree/master/pem)
  - (optional) `Root` public key
    - used for verifying signatures of TMDs/Tickets
    - binary blob with modulus and exponent (see [`nus_tools/structs/rootkey.py`](./nus_tools/structs/rootkey.py))
    - [link](http://static.hackmii.com/root-key) (sha1: `076bed301a9bcf40706330213470f53c78ff67f2`)
  - various keys (`keys.ini`, see [`keys.ini.skel`](./keys.ini.skel))
    - pretty self-explanatory, the keys are fairly easy to find on the web

## Notes
  - This is very much wip
  - It might appear to break rather easily, but the code is intentionally written in a pretty restrictive way and does very little error handling. The goal of this is to be able to discover missing fields or slightly different formats, subsequently improving the parsing logic/structs and eShop documentation
