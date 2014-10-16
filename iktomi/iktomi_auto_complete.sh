_iktomi_completion()
{
    COMPREPLY=( $(COMP_WORDS="${COMP_WORDS[*]}" \
                  COMP_CWORD=$COMP_CWORD \
                  IKTOMI_AUTO_COMPLETE=1 $1 ) )
}
complete -F _iktomi_completion -o default manage.py

_python_iktomi_completion()
{
    if [[ ${COMP_CWORD} -ge 2 ]]; then
        PYTHON_EXE=${COMP_WORDS[0]}
        echo $PYTHON_EXE | egrep "python([2-9]\.[0-9])?" >/dev/null 2>&1
        if [[ $? == 0 ]]; then
            PYTHON_SCRIPT=${COMP_WORDS[1]}
            echo $PYTHON_SCRIPT | egrep "manage.py" >/dev/null 2>&1
            if [[ $? == 0 ]]; then
                COMPREPLY=( $( COMP_WORDS="${COMP_WORDS[*]:1}" \
                               COMP_CWORD=$(( COMP_CWORD-1 )) \
                               IKTOMI_AUTO_COMPLETE=1 ${COMP_WORDS[*]} ) )
            fi
        fi
    fi
}

complete -F _python_iktomi_completion -o default python
