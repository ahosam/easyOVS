__author__ = 'baohua'

from subprocess import call,Popen,PIPE
import subprocess
import sys

import termios
from flow import Flow
from easyovs.log import output
from easyovs.util import fetchFollowingNum,fetchValueBefore,fetchValueBetween
from neutron import  get_neutron_ports

def checkBr(func):
    def wrapper(self,*arg):
        if not self.isExisted():
            output('The bridge does not exist.\n You can check available bridges using list\n')
            return None
        else:
            return func(self,*arg)
    return wrapper

class Bridge(object):
    """
    An OpenvSwitch bridge, typically is a datapath, e.g., br-int
    """
    def __init__( self, bridge):
        self.bridge = bridge
        self.flows = []
        self.flows_db= '/tmp/tmp_%s_flows' %self.bridge

    def isExisted(self):
        if not self.bridge:
            return False
        cmd="ovs-vsctl show|grep -q %s" %self.bridge
        return call(cmd,shell=True) == 0

    @checkBr
    def delFlow(self,id):
        """
        Return True or False to del the flow.
        """
        if not self.flows:
            self.updateFlows()
        if id < 0 or id >= len(self.flows):
            return False
        del_flow = self.flows[id]
        del_flow.fmtOutput()
        output("Del the flow? Y/n ")
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ICANON
        try:
           termios.tcsetattr(fd, termios.TCSADRAIN, new)
           while True:
               input = sys.stdin.read(1)
               if input == 'n' or input == 'N':
                   output('Canceled.\n')
                   return False
               elif input == 'y' or input == 'Y' or input != '\n':
                   output('\n')
                   break
               else:
                   output('\nWrong, please input [Y/n] ')
                   continue
        finally:
           termios.tcsetattr(fd, termios.TCSADRAIN, old)
        self.updateFlows(True)
        flows_db_new = self.flows_db+'.new'
        f = open(self.flows_db,'r')
        f_new = open(flows_db_new,'w')
        while True:
            lines = f.readlines(1000)
            if not lines:
                break
            for line in lines:
                flow = self.extractFlow(line)
                output(flow)
                if flow != del_flow:
                    f_new.write('%s' %line)
        f.close()
        f_new.close()
        replace_cmd="ovs-ofctl replace-flows %s %s" %(self.bridge,flows_db_new)
        result = Popen(replace_cmd,stdout=subprocess.PIPE,shell=True).stdout.read()
        return True

    @checkBr
    def updateFlows(self,to_file=False):
        """
        Update the self.flows variables with the OpenvSwitch Content.
        """
        cmd="ovs-ofctl dump-flows %s" %self.bridge
        id,flows = 0, []
        if to_file:
            f = open(self.flows_db,'w')
        result= Popen(cmd, stdout=subprocess.PIPE,shell=True).stdout.read()
        for l in result.split('\n'):
            l=l.strip()
            if l.startswith('cookie='):
                flow = self.extractFlow(l)
                if flow:
                    flows.append(flow)
                    if to_file:
                        f.write('%s\n' %l)
        if to_file:
            f.close()
        #flows=sorted(flows,key=lambda flow: flow.priority,reverse=True)
        #flows=sorted(flows,key=lambda flow: flow.table)
        flows = sorted(flows, reverse=True)
        for flow in flows:
            flow.id = id
            id += 1
        self.flows = flows

    @checkBr
    def getFlows(self):
        """
        Return a dict of flows in the bridge.
        """
        self.updateFlows()
        if len(self.flows)>0:
            return self.flows
        else:
            return {}

    def extractFlow(self,line):
        """
        Return a Flow or None, converted from a line of original output
        """
        line = line.strip()
        match,actions = '',''
        if line.startswith('cookie='):
            table = fetchFollowingNum(line,'table=')
            packet = fetchFollowingNum(line,'n_packets=')
            if table == None or packet == None:
                return None
            for fields in line.split():
                if fields.startswith('priority='):
                    priority = fetchFollowingNum(fields,'priority=')
                    if priority == None:
                        return None
                    match = fields.replace('priority=%u' %priority,'').lstrip(',')
                elif fields.startswith('actions='):
                    actions=fields.replace('actions=','').rstrip('\n')
            return Flow(self.bridge,table,packet,priority,match,actions)
        else:
            return None

    @checkBr
    def getPorts(self):
        """
        Return a dict of the ports (port, addr, tag, type) on the bridge, looks like
        {
            'qvoxxx':{
                'port':2,
                'addr':08:91:ff:ff:f3,
                'tag':1,
                'type':internal,
            }
        }
        """
        result={}
        cmd="ovs-ofctl show %s" %self.bridge
        try:
            cmd_output= Popen(cmd, stdout=subprocess.PIPE,shell=True).stdout.read()
        except Exception:
            return {}
        #output('%-8s%-16s%-16s\n' %('PORT','INTF','ADDR'))
        br_list = getBridges()
        for l in cmd_output.split('\n'):
            if l.startswith(' ') and l.find('(')>=0 and l.find(')')>=0:
                l=l.strip()
                port = fetchValueBefore(l,'(')
                intf = fetchValueBetween(l,'(',')')
                addr = l[l.find('addr:')+len('addr:'):]
                #output('%-8s%-16s%-16s\n' %(port,intf,addr))
                if self.bridge in br_list:
                    if intf in br_list[self.bridge]['Port']:
                        tag = br_list[self.bridge]['Port'][intf].get('tag','0')
                        type = br_list[self.bridge]['Port'][intf].get('type','0')
                else:
                    tag, type = '0',''
                result[intf] = {'port':port,'addr':addr,'tag':tag,'type':type}
        return result

def brDelFlow(bridge,id):
    if type(id) == str and id.isdigit():
        return Bridge(bridge).delFlow(int(id))
    elif type(id) == int:
        return Bridge(bridge).delFlow(id)
    else:
        return False

def brGetFlows(bridge):
    try:
        return Bridge(bridge).getFlows()
    except Exception:
        return None

def brIsExisted(bridge):
    """
    Return True of False of a bridge's existence.
    """
    try:
        return Bridge(bridge).isExisted()
    except Exception:
        return False

def brGetPorts(bridge):
    """
    Return a dict of all available bridges, looks like
    """
    try:
        return Bridge(bridge).getPorts()
    except Exception:
        return {}

def brList():
    """
    List available bridges.
    """
    bridges = getBridges()
    if not bridges:
        output('None bridge exists.\n')
        return
    br_info = ''
    for br in sorted(bridges.keys()):
        br_info += "%s\n" %(br)
        if bridges[br]['Port']:
            br_info += " Port:\t\t%s\n"  %(' '.join(bridges[br]['Port'].keys()))
        if bridges[br]['Controller']:
            br_info += " Controller:\t%s\n"  %(' '.join(bridges[br]['Controller']))
        if bridges[br]['fail_mode']:
            br_info += " Fail_Mode:\t%s\n"  %(bridges[br]['fail_mode'])
    output(br_info)

def brDump(bridge):
    """
    Dump the port information of a given bridges.
    """
    flows=brGetFlows(bridge)
    if flows:
        Flow.bannerOutput()
        for f in flows:
            f.fmtOutput()

def brShow(bridge):
    """
    Show information of a given bridges.
    """
    ovs_ports = brGetPorts(bridge)
    if not ovs_ports:
        output('No port is found at bridge %s\n' %bridge)
        return
    neutron_ports = get_neutron_ports()
    output('%-20s%-12s%-8s%-12s' %('Intf','Port','Tag','Type'))
    if neutron_ports:
        output('%-16s%-24s\n' %('vmIP','vmMAC'))
    else:
        output('\n')
    content=[]
    for intf in ovs_ports:
        port,tag,type = ovs_ports[intf]['port'],ovs_ports[intf]['tag'],ovs_ports[intf]['type']
        if neutron_ports and intf in neutron_ports:
            vmIP, vmMac = neutron_ports[intf]['ip_address'],neutron_ports[intf]['mac']
        else:
            vmIP,vmMac = '', ''
        content.append((intf,port,tag,type,vmIP,vmMac))
        #output('%-20s%-8s%-16s%-24s%-8s\n' %(intf,port,vmIP,vmMac,tag))
    content.sort(key=lambda x:x[0])
    content.sort(key=lambda x:x[3])
    for _ in content:
        output('%-20s%-12s%-8s%-12s' %(_[0],_[1],_[2],_[3]))
        if neutron_ports:
            output('%-16s%-24s\n' %(_[4],_[5]))
        else:
            output('\n')

def getBridges():
    """
    Return a dict of all available bridges, looks like
    {
        'br-int':{
            'Controller':[],
            'fail_mode':'',
            'Port':{
             'qvoxxx': {
                'tag':'1', //tagid
                'type':'internal', //tagid
                }
        },
    }
    """
    bridges,br={},''
    cmd='ovs-vsctl show'
    try:
        result= Popen(cmd, stdout=PIPE,shell=True).stdout.read()
    except Exception:
        return {}
    for l in result.split('\n'):
        l=l.strip().replace('"','')
        if l.startswith('Bridge '):
            br = l.lstrip('Bridge ')
            bridges[br]={}
            bridges[br]['Controller']=[]
            bridges[br]['Port']={}
            bridges[br]['fail_mode'] = ''
        else:
            if l.startswith('Controller '):
                bridges[br]['Controller'].append(l.replace('Controller ',''))
            elif l.startswith('fail_mode: '):
                bridges[br]['fail_mode']=l.replace('fail_mode: ','')
            elif l.startswith('Port '):
                phy_port = l.replace('Port ','') #e.g., br-eth0
                bridges[br]['Port'][phy_port]={'tag':0,'type':''}
            elif l.startswith('tag: '):
                bridges[br]['Port'][phy_port]['tag'] = l.replace('tag: ','')
            elif l.startswith('Interface '):
                intf = l.replace('Interface ','')
            elif l.startswith('type: '):
                bridges[br]['Port'][phy_port]['type'] = l.replace('type: ','')
    return bridges
