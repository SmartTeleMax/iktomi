_iktomi_script_check()
{
    cat $PYTHON_SCRIPT | egrep -e "iktomi" -e "cli" -e "import" -e "manage\(" >/dev/null 2>&1
    if [[ $? == 0 ]]; then
        IT_IS_IKTOMI=1
    fi
}

_iktomi_completion()
{
    PYTHON_SCRIPT=$1
    _iktomi_script_check
    if [ $IT_IS_IKTOMI -eq 1 ]; then
        COMPREPLY=( $(COMP_WORDS="${COMP_WORDS[*]}" \
                      COMP_CWORD=$COMP_CWORD \
                      IKTOMI_AUTO_COMPLETE=1 $1 ) )
    else
        COMPREPLY=()
    fi
    unset IT_IS_IKTOMI
}
complete -F _iktomi_completion -o default -o bashdefault  manage.py

_python_iktomi_completion()
{
    if [[ ${COMP_CWORD} -ge 2 ]]; then
        PYTHON_EXE=${COMP_WORDS[0]}
        echo $PYTHON_EXE | egrep "python([2-9]\.[0-9])?" >/dev/null 2>&1
        if [[ $? == 0 ]]; then
            PYTHON_SCRIPT=${COMP_WORDS[1]}
            _iktomi_script_check
            echo $PYTHON_SCRIPT | egrep "manage.py" >/dev/null 2>&1
            if [[ $? == 0 ]] && [[ $IT_IS_IKTOMI -eq 1 ]]; then
                COMPREPLY=( $( COMP_WORDS="${COMP_WORDS[*]:1}" \
                               COMP_CWORD=$(( COMP_CWORD-1 )) \
                               IKTOMI_AUTO_COMPLETE=1 ${COMP_WORDS[*]} ) )
            fi
        fi
    fi
    unset IT_IS_IKTOMI
}

complete -F _python_iktomi_completion -o default -o bashdefault python 
