from MQTT_Bridge.MQTT_Subscriber import MQTT_Subscriber

mqtt_string = "pattumi"

# tale stringa identifica la "subdirectory" nella gerarchia MQTT che verra'
# completamente scaricata dal broker e mantenuta aggiornata in parrallelo
#
# La gerarchia completa definita per ora e':
#   "pattumi/<city>/<Indirizzo>/<n_civico>/<tipo_di_rifiuto>/<sensore-attuatore>"
#
#   Esempio 1:
#
# se in input riceve "pattumi/<city>/<Indirizzo>/<n_civico>" carichera'
# i pattumi del singolo edificio a tale indirizzo
#
#   Esempio 2:
#
# "pattumi/<city>/<Indirizzo>" carichera' tutti i pattumi di tutti gli edifici in tale via
#
#   Esempio 3:
#
#se per esempio non si conosce il city di una via oppure si vuole (completamente a caso)
#includere solo i bidoni che si trovano in edifici con numero civico 1, si puo' utilizzare
#la wildcard '+' che permette di omettere dati normalmente necessari nell' esplorazione della
#gerarchia di subdirectories:
#
#   "pattumi/+/<indirizzo>" carica tutti i pattumi all' indirizzo con
#   tale nome indipendentemente dal city.
#
#   "pattumi/+/+/1" carica tutti i pattumi che appartengono a edifici con numero civico 1
#

sub = MQTT_Subscriber(mqtt_string)

# una volta inizializzato l'MQTT subscriber carichera' in automatico i pattumi ricercati che sono resi
# disponibili attraverso il metodo get_bins():

virtual_bins=sub.get_bins()

# tale oggetto e' un dizionario che contiene, per ogni stringa id di singolo edificio
#  ("pattumi/<city>/<Indirizzo>/<n_civico>"), un oggetto bin_handler.
# tale oggetto permette di accedere alle informazioni dei singoli bidoni.
# get_complete_garbage_dict() ritorna un dizionario che presenta per
# ogni singolo bidone disponibile un dizionario dei valori rilevati dai sensori e lo status
# degli attuatori

sub.print_bins()

# si puo' utilizzare print_bins di mqtt_subscriber per farsi un idea della gerarchia
# dei bidoni caricati.

sub.set_light(1,"pattumi/4567/address1/1/vetro")

# per settare la lucina led di un bidone si utilizza set_light(), il metodo
# necessita di un valore (0 spente, 1 verde, 2 rossa) e di un bin_id che e'
# semplicemente il topic che identifica anche il tipo di pattume:
#  "pattumi/<city>/<Indirizzo>/<n_civico>/<tipo_di_rifiuto>
#per comodita' tali topic sono anche le chiavi dei dizionari dei singoli bidoni
#facilitando le operazioni di publish

for bin_handler_id in virtual_bins.keys():
    garbage_dict=virtual_bins[bin_handler_id].get_complete_garbage_dict()
    for bin_id in garbage_dict.keys():
        sub.set_light(1,bin_id)

#questo loop per esempio setta a verde la lucina di tutti i bidoni

#in caso di modifiche richieste all' interfaccia modifichero' questo file e lo ripostero'

