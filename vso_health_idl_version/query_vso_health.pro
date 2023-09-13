PRO query_vso_health, skip_list = skip_list

  default, skip_list,['ChroTel','EVE','XRT','CFDT1','CFDT2','CLIMSO','OVSA']
  
  sources = read_csv('~/vso_health/vso_sources.csv',table_header=header, n_table_header=1)

  known_queries = read_csv('~/vso_health/vso_known_query_database_full.csv',table_header=header,n_table_header = 1)

  n = n_elements(sources.field1)
  status = intarr(n)

  timenowstr = anytim(systime(/seconds),fiducial = 'sys',/ccsds) 
  ; do some string manipulation to use in the output filename
  date_and_time = strsplit(timenowstr,'T',/extract)
  date_info_str = strsplit(date_and_time[0],'-',/extract)
  time_info_str = strsplit(date_and_time[1],':',/extract)
  final_timestring = date_info_str[0] + date_info_str[1] + date_info_str[2] + '_' + $
                     time_info_str[0] + time_info_str[1]

  
  
  for i=0,n-1 do begin

     ; simple error handler. If we get an error move on                  
     CATCH, error_status
     IF error_status ne 0 then begin
        print, 'Error index: ', Error_status
        print, 'Error message: ', !ERROR_STATE.MSG
        CATCH, /cancel
        wait,2
        status[i] = 9
        continue
     ENDIF

     ; skip instrumeents that are in the skip_list
     skipind = where(sources.field3[i] eq skip_list, skipcount)
     if skipcount eq 1 then begin
        status[i] = 2
        continue
     endif
     
     ; special case for AIA synoptic observations
     if (sources.field1[i] eq 'SDAC') and (sources.field3[i] eq 'AIA') then begin  
        t1_query = anytim(systime(/seconds),fiducial='sys') - (86400.0 * 4)
        t2_query = t1_query + (86400)
     ; everything else 
     endif else begin
        t1 = anytim(sources.field4[i])
        ; if source has an end date, use it
        if anytim(sources.field5[i] ne 0.0) then begin      
           t2 = anytim(sources.field5[i])
        endif else begin
           t2 = anytim(systime(/seconds),fiducial='sys')
        endelse

        dt = t2 - t1
        dt_randomize = dt * randomu(systime(/seconds))


        t1_query = t1 + dt_randomize
        ; special case for JSOC/AIA and JSOC/HMI. If query duration is too long, returns summary records
        if (sources.field1[i] eq 'JSOC') and ((sources.field3[i] eq 'AIA') OR (sources.field3[i] eq 'HMI')) then begin
           t2_query = t1 + dt_randomize + 3600.
        endif else begin
           t2_query = t1 + dt_randomize + 86400.
        endelse

     endelse
     
        
     ; print out the query for now
     print,'Query: ' + sources.field1[i] + ',' + sources.field2[i] + ',' + sources.field3[i] + $
           ',' +  anytim(t1_query,/vms) + ',' + anytim(t2_query,/vms)
        

     result = vso_search(anytim(t1_query,/vms),anytim(t2_query,/vms),provider = sources.field1[i],$
                         source = sources.field2[i], instrument = sources.field3[i],/verbose)


     
     ; evaluate result - result is an empty string if no records found
     if not keyword_set(result) then begin
        
        ; if query returned no records, try a known query
        known_ind = where((known_queries.field1 eq sources.field1[i]) and (known_queries.field2 eq sources.field2[i]) $
                          and (known_queries.field3 eq sources.field3[i]) )

        if known_ind ne -1 then begin
           t1_query = anytim(known_queries.field4[known_ind])
           t2_query = anytim(known_queries.field5[known_ind])

           print,'Random query failed. Attempting known query for: ' + sources.field1[i] + ',' + sources.field2[i] + ',' + sources.field3[i] + $
                 ',' +  anytim(t1_query,/vms) + ',' + anytim(t2_query,/vms)
           
           result = vso_search(anytim(t1_query,/vms),anytim(t2_query,/vms),provider = sources.field1[i],$
                               source = sources.field2[i], instrument = sources.field3[i],/verbose)

           if not keyword_set(result) then begin
              status[i] = 9
           endif else begin
              status[i] = 1
           endelse
        endif else begin
           status[i] = 9
        endelse

     ; if records were returned, try to download one
     endif else begin
	;special workaround of SDAC2 permissions for downloading data that uses DRMS exports - download files in place
	if ((sources.field1[i] eq 'JSOC') and ((sources.field3[i] eq 'AIA') OR (sources.field3[i] eq 'HMI'))) OR (sources.field3[i] eq 'MDI') OR $
	(sources.field3[i] EQ 'SWAP') OR (sources.field3[i] EQ 'LYRA') then begin
	    a = vso_get(result[0],filenames=dl_filename) 
	;otherwise, put all the downloaded files in a temp folder for later cleanup
	endif else begin
            a = vso_get(result[0],filenames=dl_filename, out_dir = '~/vso_health/vso_health_temp_data/')
        endelse
	if (file_exist(dl_filename) eq 0) then begin
           status[i] = 8
        endif else begin
           status[i] = 0
        endelse
        
	;special workaround of SDAC2 permissions for downloading data that uses DRMS exports - cleanup downloaded files.
	if ((sources.field1[i] eq 'JSOC') and ((sources.field3[i] eq 'AIA') OR (sources.field3[i] eq 'HMI'))) OR (sources.field3[i] eq 'MDI') OR $
	(sources.field3[i] EQ 'SWAP') OR (sources.field3[i] EQ 'LYRA') then begin
	    if (file_exist(dl_filename) eq 1) then begin
		file_delete,dl_filename
	    endif
        endif

     endelse
        

     
     
 
  endfor

  write_csv,'vso_health_checks_idl/vso_health_check_'+final_timestring+ '.csv',sources.field1,sources.field2,sources.field3,status,$
            header = ['Provider','Source','Instrument','Status']
  
  
  print,status






END
