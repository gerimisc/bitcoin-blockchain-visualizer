from blockchain import util, blockexplorer
import json, csv, requests, sys
import webbrowser
import progressbar
from time import sleep

import graphviz as gv
import functools

myapi = "54e7dc52-fdce-4569-acf6-46dd2f162624"

template = 'https://blockchain.info/address/{}?format=json'


PAGE_TOP = '''\
<html>
<head>
<body>
<p> TEST TEST </p>'''

PAGE_BOTTOM = '''\
</body>
</head>
</html>'''

n_tx = []
t_rcv = []
t_sent = []


def progress_sleepbar():
	'''
	Visual loading bar to signify the start of the program
	and to put program to sleep for a moment before 
	continuing the running of codes
	'''	
	for i in range(21):
		sys.stdout.write('\r')
		sys.stdout.write("[%-20s] %d%%" % ('='*i, 5*i))
		sys.stdout.flush()
		sleep(0.01)
	print

def get_json(address):
	'''
	Obtain JSON from website template and parsing
	them into more accessible text format in the form
	of a Python dictionary 
	'''
	url = template.format(address)
	response = requests.get(url)
	data = json.loads(response.text)

	return data


def read_csv(filename):
	'''
	Read every row in a CSV file
	appending each into a Python list
	'''
	badadd = []
	with open(filename, 'rb') as badfile:
		addreader = csv.reader(badfile)
		for row in addreader:
			badadd.extend(row)

	return badadd

def store_addr(data, param):
	'''
	Store input or output addresses to a Python list
	accordingly
	'''
	ctr = 0
	length = 0
	store = []
	final = []
	if(param == "in"):	# If system argument is "in" access specific dictionary key
		while True:
			if(length < len(data['txs'])):
				inputs = data['txs'][length]['inputs']
				if(ctr < len(inputs)):
					for i in inputs:
						try:
							addr = i['prev_out']['addr']
						except KeyError:
							continue
						store.append(str(addr))
						ctr += 1

				final.insert(length,store)
				
				length += 1
				ctr = 0
				store = []
				
			else:
				break

		return final
	else:
		while True:
			if(length < len(data['txs'])):
				inputs = data['txs'][length]['out']
				if(ctr < len(inputs)):
					for i in inputs:
						try:
							addr = i['addr']
						except KeyError:
							continue
						store.append(str(addr))
						ctr += 1

				final.insert(length,store)
				
				length += 1
				ctr = 0
				store = []
				
			else:
				break
		return final

		
def find_inputs(data, inAdd, cmpr):
	'''
	Loop the process of finding inputs to an address
	'''
	inAddresses = []
	inValues = []
	
	n = []

	ictr = 0
	length = 0
	size = len(cmpr)

	n_tx = int(data["n_tx"])
	# Convert satoshi into BTC equivalent
	t_rcv.append(int(data["total_received"])/100000000.0)
	t_sent.append(int(data["total_sent"])/100000000.0)

	for txs in data['txs']:
		if(len(txs['inputs']) == 1):
			try:
				inAddress = txs['inputs'][0]['prev_out']['addr']
				inValue = txs['inputs'][0]['prev_out']['value']
			except KeyError:
				continue
			if(inAddress != inAdd ):
				inAddresses.append(str(inAddress))
				inValues.append(int(inValue)/100000000.0)

		else:
			while True:
				inAddress = txs['inputs'][ictr]['prev_out']['addr']
				inValue = txs['inputs'][ictr]['prev_out']['value']
			
				if(inAdd in cmpr[length]): 
					pass
				else:
					
					if inAddress not in inAddresses:
						inAddresses.append(str(inAddress))
						inValues.append(int(inValue)/100000000.0)
				ictr += 1
				if(len(txs['inputs']) == ictr):
					ictr = 0
					break
		length += 1

	print "Inputs to address", inAdd, ":"
	print inAddresses
	return inAddresses, inValues, n, n_tx, t_rcv, t_sent

def find_outputs(data, inAdd, cmpr):
	'''
	Loop the process of finding inputs to an address
	'''
	outAddresses = []
	outValues = []
	n = []
	octr = 0
	ctr = 0
	length = 0

	n_tx = int(data["n_tx"])

	t_rcv.append(int(data["total_received"])/100000000.0)
	t_sent.append(int(data["total_sent"])/100000000.0)

	for txs in data['txs']:
		if(len(txs['out']) == 1):
			outAddress = txs['out'][0]['addr']
			outValue = int(txs['out'][0]['value'])

			if(outAddress != inAdd):
				outAddresses.append(str(outAddress))
				outValues.append(int(outValue)/100000000.0)
				length += 1

		else:
			while True:
				try:
					outAddress = txs['out'][octr]['addr']
					outValue = txs['out'][octr]['value']
				except KeyError:
					continue
				if(inAdd in cmpr[length] or outAddress == inAdd): 
					pass
				else:
					outAddresses.append(str(outAddress))
					outValues.append(int(outValue)/100000000.0)
				octr += 1
				if(len(txs['out']) == octr):
					octr = 0
					break
			length += 1
	print "Outputs from address", inAdd, ":"
	print outAddresses, n_tx
	return outAddresses, outValues, n, n_tx, t_rcv, t_sent


def plot(start, txc, txamt, addrc, direct, inFile, flow=None, col=None):
	'''
	Plotting of nodes and edges given
	addresses, tx amount, direction and file
	'''

	# Customization of nodes and edges
	g.node_attr.update(fillcolor='#006699', style='filled', color="white", fontcolor="white", shape='plaintext', ranksep='0.75', nodesep='0.75', size='30')
	g.edge_attr.update(color="white", fontcolor="red", weight="1.2")
	g.graph_attr.update(splines="ortho", bgcolor="black", fontcolor="white")

	c = 0
	counter = 0
	
	for a,b in map(None, addrc, txamt):
		# If a resultant address matches one of the bad list, flags by changing node shape
		if(a in inFile):
			counter = inFile.index(a)
			g.node(a, shape="record", xlabel="{"+str(a)+"|Type: "+inFile[counter+1]+"|Details: "+inFile[counter+2]+"}", penwidth=str(3), fillcolor='yellow', fontcolor="black", color="red")
			print "SUSPECT FOUND AT", a, "!!!"
			# checks if the transacted amount is larger than the previous one - Change addresses
			if(b > c):
				g.edge(start, a, xlabel=str(round(b, 4)) +' BTC', fontsize="16.0", dir=direct, weight="100")
				c = b
			else:
				g.edge(start, a, xlabel=str(round(b, 4)) +' BTC', fontsize="16.0", dir=direct, color="black")
				c = b
			
			
		else:
			# checks for tx amount and flags it by changing the node characteristics if minimum is met
			if(b > flag):
				g.node(a, label=str(a), penwidth=str(3), fontsize='20', fillcolor='yellow', fontcolor='black', shape='oval')
			else:
				g.node(a, label=str(a), penwidth=str(3))

			if(b < c and flow == "bothdir" and col=="in"):
				g.edge(start, a, xlabel=str(round(b, 4)) +' BTC', fontsize="16.0", dir=direct, color="black")
				c = b
			elif(b < c and flow == "bothdir" and col=="out"):
				g.edge(start, a, xlabel=str(round(b, 4)) +' BTC', fontsize="16.0", dir=direct, color="black")
				c = b
			else:
				g.edge(start, a, xlabel=str(round(b, 4)) +' BTC', fontsize="16.0", dir=direct, color="black")
				c = b
		counter +=2
		
	return g

def track(data, inAdd, cmpr, flow):
	'''
	Responsible for repeatedly replacing previous 
	address list to the next
	'''
	if (flow == "in"):
		inAddresses, values, n, n_tx, t_rcv, t_sent = find_inputs(data, inAdd, cmpr)
		return inAddresses, values, n, n_tx, t_rcv, t_sent
	else:
		outAddresses, values, n, n_tx, t_rcv, t_sent = find_outputs(data, inAdd, cmpr)
		return outAddresses, values, n, n_tx, t_rcv, t_sent

if __name__ == '__main__':
	try:
		# Assignment of necessary system arguments
		if(len(sys.argv) == 5):
			flow = sys.argv[1] # direction of inspection
			inAdd = sys.argv[2] # starting address
			depth = int(sys.argv[3]) # depth search
			flag = float(sys.argv[4]) # Minimum amount for node flagging
		elif(len(sys.argv) == 6):
			flow = sys.argv[1]
			inAdd = sys.argv[2]
			depth = int(sys.argv[3])
			inFile = sys.argv[4] # CSV file object
			flag = float(sys.argv[5])
			try:
				inFile = read_csv(sys.argv[4]) # store output of read_csv to an object list inFile
				print("Reading ", sys.argv[4])
			except IOError:
				sys.exit("No such file exists. Please check filename")
		else:
			sys.exit('Usage: python viztool.py <in/out> <address> <depth> <*file> <amount>')

	except IndexError:
		sys.exit('Usage: python viztool.py <in/out> <address> <depth> <*file>')
	g = gv.Digraph(format='DOT')
	z = 0
	ctr = 1
	ctri = 1
	ctro = 1
	next = []
	nexts = []
	nexti = []
	nexto = []
	if (flow == "in" and depth >= 1):
		print "===== Searching depth 0 ====="
		data = get_json(inAdd)	# Obtain initial source of address at invocation
		progress_sleepbar()
		cmpr = store_addr(data, "in")
		inAddresses, values, n, n_tx, t_rcv, t_sent = find_inputs(data, inAdd, cmpr)
		g.node(inAdd)	# Draw initial node

		if(len(sys.argv) == 5):
			g = plot(inAdd, n_tx, values, inAddresses, "back", inFile)
			print("length of sys argv is 5")
			
		else:
			g = plot(inAdd, n_tx, values, inAddresses, "back")

		if(depth > 1): # Repeats above function if depth search is more than one
			print "===== Begin breadth tracking of inputs ====="
			while True:
				if(ctr == 1):
					print "===== Searching depth",ctr, "====="
					# For every address, store the inputs of the addres to a ist
					for i in inAddresses:
						data = []
						data = get_json(i)
						cmpr = store_addr(data, "in")
						nAddr, nValue, nN, n_tx, t_rcv, t_sent = track(data, i, cmpr, "in")
						next.extend(nAddr)

						g = plot(i, n_tx, nValue, nAddr, "back", inFile)
					ctr += 1


				if(ctr <= depth):
					print "===== Searching depth",ctr, "====="
					for i in next[0:]:
						data = []
						data = get_json(i)
						cmpr = store_addr(data, "in")

						nAddr, nValue, nN, n_tx, t_rcv, t_sent = track(data, i, cmpr, "in")
						next.extend(nAddr)

						g = plot(i, n_tx, nValue, nAddr, "back", inFile)
						next.pop(0)

					ctr += 1

				else:
					break
		g.render('img/g1') # renders plotted nodes and edges into a graph

	elif (flow == "out" and depth >= 1):
		data = get_json(inAdd)
		progress_sleepbar()
		cmpr = store_addr(data, "out")
		outAddresses, values, n, n_tx, t_rcv, t_sent = find_outputs(data, inAdd, cmpr)

		g.node(inAdd)

		if(len(sys.argv) == 6):
			g = plot(inAdd, n_tx, values, outAddresses, "front", inFile)
			
		else:
			g = plot(inAdd, n_tx, values, outAddresses, "front")
		

		if(depth > 1):
			print "===== Begin breadth tracking of outputs ====="
			while True:
				if(ctr == 1):
					print "===== Searching depth",ctr, "====="
					for i in outAddresses:
						data = []
						data = get_json(i)
						cmpr = store_addr(data, "out")
						nAddr, nValue, nN, n_tx, t_rcv, t_sent = track(data, i, cmpr, "out")
						next.extend(nAddr)


						g = plot(i, n_tx, nValue, nAddr, "front", inFile)
					ctr += 1

				if(ctr <= depth):
					print "===== Searching depth",ctr, "====="
					print "NEXT CONTENT: ",next
					print "ctr: ",ctr 
					for i in next[0:]:
						data = []
						data = get_json(i)
						cmpr = store_addr(data, "out")
						nAddr, nValue, nN, n_tx, t_rcv, t_sent = track(data, i, cmpr, "out")
						next.extend(nAddr)

						g = plot(i, n_tx, nValue, nAddr, "front", inFile)
						next.pop(0)

					ctr += 1

				else:
					break
		g.render('img/g1')

	elif(flow == "both" and depth >=1):
		print "===== Searching depth 0 ====="
		data = get_json(inAdd)
		progress_sleepbar()
		cmprin = store_addr(data, "in")
		cmprout = store_addr(data, "out")
		inAddresses, valuesi, ni, ni_tx, ti_rcv, ti_sent = find_inputs(data, inAdd, cmprin)
		outAddresses, valueso, no, no_tx, to_rcv, to_sent = find_outputs(data, inAdd, cmprout)

		g.node(inAdd)
		
		if(len(sys.argv) == 5):
			g = plot(inAdd, ni_tx, valuesi, inAddresses, "back", inFile)
			g = plot(inAdd, no_tx, valueso, outAddresses, "front", inFile)
			print("length of sys argv is 5")
			
		else:
			g = plot(inAdd, ni_tx, valuesi, inAddresses, "back")
			g = plot(inAdd, no_tx, valueso, outAddresses, "front")

		if(depth > 1):
			print "===== Begin breadth tracking of inputs ====="
			while True:
				if(ctri == 1):
					print "===== Searching depth",ctr, "====="
					for i in inAddresses:
						datai = []
						datai = get_json(i)
						cmprin = store_addr(data, "in")
						cmprout = store_addr(data, "out")
						nAddri, nValuei, nNi, ni_tx, ti_rcv, ti_sent = track(data, i, cmprin, "in")
						nAddro, nValueo, nNo, no_tx, to_rcv, to_sent = track(data, i, cmprout, "out")
						nexts.extend(nAddri)
						nexts.extend(nAddro)
						g = plot(i, ni_tx, nValuei, nAddri, "back", inFile)
						g = plot(i, no_tx, nValueo, nAddro, "front", inFile)
					ctri += 1
				
				if(ctri <= depth):
		
					print "===== Searching depth",ctr, "====="

					for i in nexts[0:]:
						datai = []
						datao = []
						datai = get_json(i)
						datao = get_json(i)
						cmpri = store_addr(datai, "in")
						cmpro = store_addr(datao, "out")
						nAddri, nValuei, nNi, ni_tx, ti_rcv, ti_sent = track(data, i, cmpri, "in")
						nAddro, nValueo, nNo, no_tx, to_rcv, to_sent = track(data, i, cmpro, "out")
						nexts.extend(nAddri)
						nexts.extend(nAddro)
						g = plot(i, ni_tx, nValuei, nAddri, "back", inFile)
						g = plot(i, no_tx, nValueo, nAddro, "front", inFile)
						nexts.pop(0)

					ctri += 1

				else:
					break
		
		
		g.render('img/g1')
	else:
		print "depth: min value is 1"
		sys.exit('Usage: python viztool.py <in/out> <address> <depth>')


	progress_sleepbar()
	print "g1.svg can be found in img/g1"
