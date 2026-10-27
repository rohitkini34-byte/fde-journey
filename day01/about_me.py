"""Day 1: about me — f-strings, core types, arithmetic and float input."""

name = "Rohit Kini"
role = "Forward Deployed Engineer (in training)"
years_in_cms = 7
is_career_switch = True
start_date = "22 Oct 2026"

# 16-week plan, 5 hours a day, 7 days a week
weeks = 16
days_per_week = 7
hours_per_day = 5
total_plan_hours = weeks * days_per_week * hours_per_day   # int * int -> int

print("=== About me ===")
print(f"Name:              {name}")
print(f"Target role:       {role}")
print(f"CMS experience:    {years_in_cms} years")
print(f"Career switch:     {is_career_switch}")
print(f"Started on:        {start_date}")
print()
print("=== Types ===")
print(f"name             -> {type(name).__name__}")
print(f"years_in_cms     -> {type(years_in_cms).__name__}")
print(f"is_career_switch -> {type(is_career_switch).__name__}")
print(f"total_plan_hours -> {type(total_plan_hours).__name__}")
print()
print("=== The plan ===")
print(f"{weeks} weeks x {days_per_week} days x {hours_per_day} h = {total_plan_hours} hours")
print(f"That is {total_plan_hours // 24} full days and {total_plan_hours % 24} hours of study")
print()

# input() always returns a str, so convert it before doing maths
hours_studied = float(input("How many hours have you studied so far? "))
remaining = total_plan_hours - hours_studied
percent_done = hours_studied / total_plan_hours * 100

print(f"Hours studied:   {hours_studied:.1f}")
print(f"Hours remaining: {remaining:.1f}")
print(f"Progress:        {percent_done:.1f}%")
