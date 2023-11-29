export TO_DELETE_PATH=/home/jm/signal_duplicates
mkdir -p ${TO_DELETE_PATH}
DRY_RUN=1 DUP_WITHIN=1 \
    python3 photo-utils/find_dups.py\
    phone_dump/signal phone_dump_july22_2023/signal