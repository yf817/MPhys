#!/bin/sh
echo \# Bash script to perform registration using elastix

cwd="/mnt/e/Mphys/"
base_dir="/mnt/e/Mphys/NiftyPatients"
fixed_ref="PlanningCT"
moving_ref="PET"
out_dir="/mnt/e/Mphys/ElastixReg"

if [ -d ${out_dir}  ]; then
  rm -rf ${out_dir}
fi
mkdir ${out_dir}
mkdir ${out_dir}/Rigid/
mkdir ${out_dir}/Non-Rigid/
mkdir ${out_dir}/DVF/
# Loop over all patients saved in Nifty Patients
for filepath in `(ls -f ${base_dir}/${fixed_ref}/*.nii )`; do
  #  Get patient name from filename
  filename=$(basename -- "$filepath")
  image="${filename%.*}"
  echo $image
  # Make required directories
  mkdir ${out_dir}/DVF/${image}
  mkdir ${out_dir}/Rigid/${image}
  mkdir ${out_dir}/Non-Rigid/${image}
  # Perform Registration, first affine then b-spline
  elastix -f ${base_dir}/${fixed_ref}/${image} -m ${base_dir}/${moving_ref}/${image} -p ${cwd}/Affine-parameter-file.txt  -out ${out_dir}/Rigid/${image}
  elastix -f ${base_dir}/${fixed_ref}/${image} -m ${out_dir}/Rigid/${image}/result.0.nii -p ${cwd}/B-Spline-parameter-file.txt  -out ${out_dir}/Non-Rigid/${image}
  # Generate deformation field from affine transform file
  transformix -def all -tp ${out_dir}/Non-Rigid/${image}/TransformParameters.0.txt -out ${out_dir}/DVF/${image}
done
