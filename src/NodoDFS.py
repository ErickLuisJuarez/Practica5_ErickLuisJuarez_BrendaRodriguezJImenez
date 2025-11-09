import simpy
from Nodo import *
from Canales.CanalRecorridos import *
import time
from random import randint

class NodoDFS(Nodo):
    ''' Implementa la interfaz de Nodo para el algoritmo de Broadcast.'''

    def __init__(self, id_nodo, vecinos, canal_entrada, canal_salida, num_nodos):
        ''' Constructor de nodo que implemente el algoritmo DFS. '''
        super().__init__(id_nodo, vecinos, canal_entrada, canal_salida)
        self.padre = None
        self.hijos = []
        self.eventos = []  # lista de eventos: valor del reloj, tipo de evento (E/R), mensaje, emisir y receptor
        self.reloj = [0] * num_nodos  # reloj vectorial

    def actualizar_al_recibir(self, reloj_recibido):
        ''' Funcion auxiliar que lleva a cabo el procedimiento de cuando
        un nodo recibe un mensaje '''
        if reloj_recibido == None:
            self.reloj[self.id_nodo] += 1  # incrementa su propio reloj
            return tuple(self.reloj)  # lo devuelve en forma de tupla inmutable
        else:
            for i in range(len(self.reloj)):
                # toma siempre el maximo entre el componente de su propio reloj y el recibido
                self.reloj[i] = max(self.reloj[i], reloj_recibido[i])
            self.reloj[self.id_nodo] += 1  # incrementa su propio reloj
            return tuple(self.reloj)

    def enviar_msj(self, env, mensaje, receptor):
        ''' Funcion auxiliar para enviar un mensaje con el reloj adjunto '''
        self.reloj[self.id_nodo] += 1  # el reloj se incrementa en 1 al enviar mensajes
        copia_reloj = tuple(self.reloj)  # obtenemos una copia del reloj para adjuntarla al mensaje
        msj_reloj = mensaje + (copia_reloj,)  # agregando copia_reloj a la tupla mensaje
        # se agrega el evento de envio del mensaje, con todos los componentes requeridos
        self.eventos.append((copia_reloj, "E", msj_reloj, self.id_nodo, receptor))
        yield env.timeout(randint(1, 3))  # tiempo aleatorio entre envio de mensajes
        yield self.canal_salida.envia(msj_reloj, [receptor])  # se envia el mensaje

    def dfs(self, env):
        ''' Algoritmo DFS (con relojes vecotirales). '''
        if self.id_nodo == 0:
            yield self.canal_entrada.put(("START", None))

        while True:
            mensaje = yield self.canal_entrada.get()
            yield env.timeout(randint(1, 3))  # tiempo aleatorio entre recepcion de mensajes
            tipo = mensaje[0]

            # when START() is received do
            if tipo == "START":
                reloj_nuevo = self.actualizar_al_recibir(None)  # actualizamos el reloj
                self.padre = self.id_nodo
                self.hijos = []
                self.visitados = set()
                
                if not self.vecinos:
                    # si no hay vecinos, terminamos
                    continue
                else:
                    # let k in neighbors_i; send GO() to p_k
                    for v in self.vecinos:
                        if v not in self.visitados:
                            k = v
                            break
                    yield env.process(self.enviar_msj(env, ("GO", self.id_nodo), k))
            
            # when GO() is received from p_j do
            elif tipo == "GO":
                j = mensaje[1]
                reloj_recibido = mensaje[-1]  # obtenemos el reloj vectorial adjunto en el mensaje
                reloj_nuevo = self.actualizar_al_recibir(reloj_recibido)  # actualizamos el reloj
                # se agrega el evento de recepcion del mensaje, con todos los componentes requeridos
                self.eventos.append((reloj_nuevo, "R", mensaje, j, self.id_nodo))

                if self.padre == None:
                    self.padre = j
                    self.hijos = []
                    self.visitados = set([j])

                    if self.visitados == set(self.vecinos):
                        # if(visited_i = neighbors_i) then send BACK(yes) to p_j
                        yield env.process(self.enviar_msj(env, ("BACK", self.id_nodo, "yes"), j))
                    else:
                        # else let k in neighbors_i \ visied_i; send GO() to p_k
                        for v in self.vecinos:
                            if v not in self.visitados:
                                k = v
                                break
                        yield env.process(self.enviar_msj(env, ("GO", self.id_nodo), k))
                else:
                    # else send BACK(no) to p_j
                    yield env.process(self.enviar_msj(env, ("BACK", self.id_nodo, "no"), j))

            # when BACK(resp) is received from p_j do
            elif tipo == "BACK":
                j = mensaje[1]
                resp = mensaje[2]
                reloj_recibido = mensaje[-1]  # obtenemos el reloj vectorial adjunto en el mensaje
                reloj_nuevo = self.actualizar_al_recibir(reloj_recibido)  # actualizamos el reloj
                # se agrega el evento de recepcion del mensaje, con todos los componentes requeridos
                self.eventos.append((reloj_nuevo, "R", mensaje, j, self.id_nodo))

                if resp == "yes":
                    # if(resp = yes) then children_i = children_i u {j} end if;
                    if j not in self.hijos:
                        self.hijos.append(j)
                self.visitados.add(j)

                if self.visitados == set(self.vecinos):
                    # if(visited_i = neighbors_i)
                    if self.padre == self.id_nodo:
                        # then if(parent_i = i) then the traversal is terminated
                        continue
                    else:
                        # else send BACK(yes) to p_(parent_i)
                        yield env.process(self.enviar_msj(env, ("BACK", self.id_nodo, "yes"), self.padre))
                else:
                    # else let k in neighnors_i \ visited_i; send GO() to p_k
                    for v in self.vecinos:
                        if v not in self.visitados:
                            k = v
                            break
                    yield env.process(self.enviar_msj(env, ("GO", self.id_nodo), k))
