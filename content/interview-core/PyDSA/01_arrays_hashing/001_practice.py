list_comprehension = [x**2 for x in range(10)]

nums = [1,2,3]
n = len(nums)
duplicate_list = [nums[j % n] for j in range(3 * n)]



print(duplicate_list)