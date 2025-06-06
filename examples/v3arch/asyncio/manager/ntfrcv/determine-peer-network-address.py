"""
Receive notifications noting peer address
+++++++++++++++++++++++++++++++++++++++++

Receive SNMP TRAP/INFORM messages with the following options:

* SNMPv1/SNMPv2c
* with SNMP community "public"
* over IPv4/UDP, listening at 127.0.0.1:162
* use observer facility to pull lower-level request details from SNMP engine
* print received data on stdout

Either of the following Net-SNMP commands will send notifications to this
receiver:

| $ snmptrap -v2c -c public 127.0.0.1:162 123 1.3.6.1.6.3.1.1.5.1 1.3.6.1.2.1.1.5.0 s test

"""  #
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

# Create SNMP engine with autogenernated engineID and pre-bound
# to socket transport dispatcher
snmpEngine = engine.SnmpEngine()

# Transport setup

# UDP over IPv4, first listening interface/port
config.add_transport(
    snmpEngine,
    udp.DOMAIN_NAME + (1,),
    udp.UdpTransport().open_server_mode(("127.0.0.1", 162)),
)

# SNMPv1/2c setup

# SecurityName <-> CommunityName mapping
config.add_v1_system(snmpEngine, "my-area", "public")


# Callback function for receiving notifications
# noinspection PyUnusedLocal,PyUnusedLocal
def cbFun(snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    # Get an execution context...
    execContext = snmpEngine.observer.getExecutionContext(
        "rfc3412.receiveMessage:request"
    )

    # ... and use inner SNMP engine data to figure out peer address
    print(
        'Notification from {}, ContextEngineId "{}", ContextName "{}"'.format(
            "@".join([str(x) for x in execContext["transportAddress"]]),
            contextEngineId.prettyPrint(),
            contextName.prettyPrint(),
        )
    )
    for name, val in varBinds:
        print(f"{name.prettyPrint()} = {val.prettyPrint()}")


# Register SNMP Application at the SNMP engine
ntfrcv.NotificationReceiver(snmpEngine, cbFun)

snmpEngine.transport_dispatcher.job_started(1)  # this job would never finish

# Run I/O dispatcher which would receive queries and send confirmations
try:
    snmpEngine.open_dispatcher()
except:
    snmpEngine.close_dispatcher()
    raise
