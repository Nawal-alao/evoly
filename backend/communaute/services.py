import string

from .models import MotInterdit


def contient_mot_interdit(texte):
    """
    Retourne True si au moins un mot du texte correspond exactement
    (une fois nettoyé de sa ponctuation) à un MotInterdit enregistré.
    Utilise des sets pour rester performant même avec beaucoup de mots
    interdits (voir la discussion sur le hachage qu'on a eue ensemble).
    """
    mots_interdits = {m.lower() for m in MotInterdit.objects.values_list("mot", flat=True)}
 
    mots_du_texte = {
        mot.strip(string.punctuation).lower()
        for mot in texte.split()
    }
 
    return bool(mots_interdits & mots_du_texte)