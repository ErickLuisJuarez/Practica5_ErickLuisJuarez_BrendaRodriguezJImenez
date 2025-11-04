import simpy
from Nodo import *
from Canales.CanalRecorridos import *
from random import randint

class NodoBroadcast(Nodo):
    def __init__(self, id_nodo: int, vecinos: list, canal_entrada: simpy.Store,
                 canal_salida: simpy.Store):
        super().__init__(id_nodo,vecinos,canal_entrada,canal_salida)
        self.mensaje = None
        self.reloj = 0
        self.eventos = []

    def broadcast(self, env: simpy.Environment, data="Mensaje"):
        if self.id_nodo == 0: #Si el nodo es 0
            yield env.timeout(randint(1, 3)) #Se espera un tiempo aleatorio para comenzar
            self.reloj += 1 #Se aumenta el reloj logico ya que se va realizar un evento
            self.mensaje = data #Se guarda el mensaje que se va propagar por la red

            for v in self.vecinos: #Se recorre a todo slos vecinos que se va enviar el mensaje
                yield env.timeout(randint(1, 3)) #Se espera un tiempo aleatorio para simular la asincronia
                self.reloj += 1 #Se incrementa el reloj por cada envio ya que un evio es un evento
                msg = (data, self.reloj, self.id_nodo) #Se empaqueta el mensaje con el nodo que hizo el envio y el reloj
                self.eventos.append((self.reloj, "E", data, self.id_nodo, v)) #Se marca el evento como envio
                yield self.canal_salida.envia(msg, [v])#Se envia el mensaje al vecino

        while True: #Cualquier nodo
            mensaje, reloj_remitente, emisor = yield self.canal_entrada.get() #Se espera que llegue un mensaje por el canal de entrada
            self.reloj = max(self.reloj, reloj_remitente) + 1 #Cuando s erecibe el mensaje, se actualiza el reloj
            self.eventos.append((self.reloj, "R", mensaje, emisor, self.id_nodo)) #Se marca el evento como recepcion
            if self.mensaje is None: #Si el nodo no ha recibido ningun mensaje
                self.mensaje = mensaje #Se guardael mensaje
                yield env.timeout(randint(1, 3)) #Se espera un pequeño tiempo aleatorio antes de reenviar
                
                for v in self.vecinos: #Reeenvia el mensaje a todos los vecinos
                    if v != emisor:  #Si el vecino no es quien lo mando
                        self.reloj += 1 #Se incrementa el reloj por cada envio ya que un evio es un evento
                        msg = (mensaje, self.reloj, self.id_nodo) #Se empaqueta el mensaje con nodo que lo envio y el nuevo reloj
                        self.eventos.append((self.reloj, "E", mensaje, self.id_nodo, v)) #Se marca el evento como envio
                        yield env.timeout(randint(1, 3)) #Se espera un tiempo aleatorio paera reenviar
                        yield self.canal_salida.envia(msg, [v]) #Se envia el mensaje al vecino