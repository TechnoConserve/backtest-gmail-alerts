from alert_parse import HistAlert

def main():
	hist = HistAlert()
	syms = []
	dates = []

	for index in range(0, len(hist.return_message_list())):
		target = hist.return_target(index)

		dates.append(target[0])
		syms.append(target[1])

	#print(syms)
	#print(dates)

	while len(syms) > len(set(syms)):
		for sym in syms:
			indices = [i for i, x in enumerate(syms) if x == sym]
			if len(indices) < 2:
				# This symbol is already unique
				continue
			#print("Indices: ", indices)
			tuplist = [(i, x) for i, x in enumerate(dates) if i in indices]
			date_check = [x[1] for x in tuplist]
			#print("Dates to check: ", date_check)
			mini = min(date_check)
			#print("Minimum date: ", mini)

			# pop the index we want to keep from indices then remove the others
			for tup in tuplist:
				if mini == tup[1]:
					index = tup[0]
			print("Removing: ", indices.pop(indices.index(index)))
			syms = [x for i, x in enumerate(syms) if i not in indices]
			dates = [x for i, x in enumerate(dates) if i not in indices]

			# Break so we can refresh the for loop with the changed list of syms
			break

	#print(syms)
	#print(dates)


if __name__ == '__main__':
	main()