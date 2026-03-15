weight = int(input())

for i in range(1, weight):
    if (weight - 2 * i) % 2 == 0 and weight - 2 * i > 0:
        print("YES")
        break
else:
    print("NO")