#!/usr/bin/env python
#coding=utf8


import libvirt
import MySQLdb
import libvirt,os,sys
from xml.etree import ElementTree


openstack_db_host='10.0.0.51'
openstack_db_user='root'
openstack_db_pwd='mysql'

uri='qemu:///system'

conn=libvirt.open(None)

user_id='5f93f059173248f0b3058a906dc07a0a'
project_id='c5b0af91883d47298e20b421f353695d'
power_stata=0
vm_state='active'
task_state='NULL'
default_ephemeral_device='NULL'
eohemeral_gb='NULL'


def db_cmd(host=openstack_db_host,user=openstack_db_user,passwd=openstack_db_pwd,\
    db="nova",sql="None",select=True):
    conn=MySQLdb.connect(host=host,user=user,passwd=passwd,db=db,\
        use_unicode=True,charset="utf8")
    cursor=conn.cursor()
    line=cursor.execute(sql)
    if not select:
        conn.commit()
        conn.close()
        return line
    datas=cursor.fetchall()
    conn.commit()
    conn.close()
    return datas


def get_devices(dom,path,devs):
    tree=ElementTree.fromstring(dom.XMLDesc(0))
    devices=[]
    for target in tree.findall(path):
        dev=target.get(devs)
        if not dev in devices:
            devices.append(dev)
    return devices

def get_doms_id():
	return conn.listDomainsID()


def get_doms_info():
	for dom_id in get_doms_id():
		dom=conn.lookupByID(dom_id)
		print dom.name(),
		if dom.name().startswith('instance'):
			print 'OpenStack instance, pass'
			continue
		if dom.isActive:
			power_state = 1
			vm_state='active'
		current_instance_id_sql='select max(id) from instances;'
		instance_id=hex(db_cmd(sql=current_instance_id_sql)[0][0]+1)[2:-1]
		instance_name='instance-'+'0'*(8-len(instance_id))+instance_id
		print 'change instance %s to %s'  % (dom.name(),instance_name)
		vcpus=dom.maxVcpus()
		memory=dom.info()[2]/1024
		hostname=display_name=dom.name()
		launched_on = host = conn.getHostname()
		instance_type_id=1
		uuid=dom.UUIDString()
		root_device_name='/dev/'+get_devices(dom,"devices/disk/target","dev")[0]
		root_gb=dom.blockInfo(get_devices(dom,"devices/disk/target","dev")[0],0)[0]/1024/1024/1024
		migrate_sql="insert into instances (created_at,updated_at,deleted,user_id,project_id,\
						power_state,vm_state,memory_mb,vcpus,hostname,host,\
						display_name,launched_on,instance_type_id,uuid,root_device_name,\
						task_state,default_ephemeral_device,root_gb,ephemeral_gb) values \
						(now(),now(),'%d','%s','%s',%d,'%s','%s','%s','%s','%s','%s',\
						'%s','%d','%s','%s',%s,'%s','%s','%d')" % \
						(0,user_id,project_id,1,vm_state,memory,vcpus,hostname,host,\
						display_name,launched_on,6,uuid,root_device_name,'NULL','NULL',root_gb,0)
		db_cmd(sql=migrate_sql)
		tree=ElementTree.fromstring(dom.XMLDesc(0))
		tree[0].text=instance_name
		tree=ElementTree.ElementTree(tree)
		tree.write('/tmp/%s.xml' % instance_name ,encoding='utf-8')
		print "virsh undefine %s" % dom.name()
		dom.undefine()
		print "shut off the instance %s" % dom.name()
		dom.destroy()
		conn.defineXML("".join(file('/tmp/%s.xml' % instance_name, 'r').readlines()))
		print "restart the instance %s(%s)" % (instance_name,dom.name())
		dom.create()
if __name__=='__main__':
	get_doms_info()
