def allocate_seats(total_seats, label_to_pop):
    total_pop = sum(label_to_pop.values())
    label_to_seats = {}
    label_to_rem = {}
    total_seats_i = 0
    for label, pop in label_to_pop.items():
        seats_r = total_seats * pop / total_pop
        seats_i = (int)(seats_r)
        total_seats_i += seats_i
        rem = seats_r - seats_i

        label_to_seats[label] = seats_i
        label_to_rem[label] = rem

    excess_seats = total_seats - total_seats_i
    sorted_labels_and_rem = sorted(
        label_to_rem.items(),
        key=lambda x: -x[1],
    )

    for i in range(0, excess_seats):
        label = sorted_labels_and_rem[i][0]
        label_to_seats[label] += 1

    return label_to_seats
