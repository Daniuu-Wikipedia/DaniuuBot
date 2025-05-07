import Revdel_patrol
import IPBLOK_patrol
import REGBLOK_patroller
import time

# First job: run Revdel patrol
print('Doing REVDEL')
rp = Revdel_patrol.Revdel()
rp()
print('DONE REVDEL')
del rp

# Go to sleep for 5 seconds
time.sleep(5)

# Second job: run IPBLOK patrol
print('Doing IPBLOK')
ip = IPBLOK_patrol.IPBLOK()
ip()
print('DONE IPBLOK')
del ip

# Third job: run REGBLOK patrol
print('Doing REGBLOK')
rb = REGBLOK_patroller.REGBLOK()
rb()
del rb  # Clear some memory
print('DONE REGBLOK')
# End of script
